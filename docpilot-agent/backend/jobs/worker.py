"""
Celery Tasks for DocPilot Pipeline
Handles async processing of repository analysis and documentation generation
"""
import os
import shutil
from celery import shared_task, chain, group
from celery.utils.log import get_task_logger
from git import Repo, GitCommandError
import json
from backend.db.data import user_repo_db
from backend.agents.parser.parser_manager import ParserManager
from backend.agents.kg_builder.openAiKG import generate_cypher_from_ast
from backend.agents.kg_builder.Kg_reader import dataRetrive
from backend.agents.docgen.doc_generator import generate_docs
from backend.db.neo4j_connect import driver
from backend.core.config import settings
from backend.db.repo_queries import save_documentation, get_repo_by_url

logger = get_task_logger(__name__)

# Initialize parser manager
parser_manager = ParserManager()


@shared_task(bind=True, name='tasks.clone_repository')
def clone_repository(self, proj_name, repo_url, branch, github_token):
    """
    Task 1: Clone or update repository from GitHub
    """
    try:
        logger.info(f"Starting clone task for project: {proj_name}")
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        basePath = os.path.join(BASE_DIR, "UserRepos")
        os.makedirs(basePath, exist_ok=True)
        
        path = os.path.join(basePath, proj_name)
        
        # Add GitHub token to clone URL
        clone_url = repo_url
        if clone_url.startswith("https://"):
            clone_url = clone_url.replace(
                "https://",
                f"https://{github_token}@"
            )
        
        try:
            if not os.path.exists(path):
                logger.info(f"Cloning repository to {path}")
                Repo.clone_from(clone_url, path, branch=branch)
            else:
                logger.info(f"Updating existing repository at {path}")
                repo_obj = Repo(path)
                repo_obj.git.reset("--hard")
                repo_obj.git.clean("-fd")
                repo_obj.remotes.origin.pull()
        except GitCommandError as e:
            logger.error(f"Git error: {str(e)}")
            raise Exception(f"Git operation failed: {str(e)}")
        
        # Store in memory DB
        user_repo_db[proj_name] = {
            "local_path": path,
            "repo_url": repo_url,
            "branch": branch
        }
        
        logger.info(f"Repository cloned successfully: {proj_name}")
        return {
            "status": "success",
            "project": proj_name,
            "path": path,
            "message": "Repository cloned/updated successfully"
        }
    
    except Exception as e:
        logger.error(f"Clone task failed: {str(e)}")
        raise


@shared_task(bind=True, name='tasks.parse_repository')
def parse_repository(self, clone_result, proj_name):
    """
    Task 2: Parse all code files in the repository using language-specific parsers
    Receives result from clone task as first argument
    """
    try:
        logger.info(f"Starting parse task for project: {proj_name}")
        
        if proj_name not in user_repo_db:
            raise Exception(f"Project {proj_name} not found in repository database")
        
        repo_path = user_repo_db[proj_name]["local_path"]
        
        if not os.path.isdir(repo_path):
            raise Exception(f"Repository directory not found: {repo_path}")
        
        parsed_files = []
        
        # Walk through all files in repository
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.next'}]
            
            for f in files:
                file_path = os.path.join(root, f)
                
                try:
                    result = parser_manager.parse(file_path)
                    if result:
                        parsed_files.append(result)
                except Exception as e:
                    logger.warning(f"Failed to parse {file_path}: {str(e)}")
                    continue
        
        logger.info(f"Parse task complete: {len(parsed_files)} files parsed for {proj_name}")
        
        return {
            "status": "success",
            "project": proj_name,
            "total_files": len(parsed_files),
            "data": parsed_files,
            "message": f"Successfully parsed {len(parsed_files)} files"
        }
    
    except Exception as e:
        logger.error(f"Parse task failed: {str(e)}")
        raise


@shared_task(bind=True, name='tasks.generate_cypher')
def generate_cypher(self, parse_result, proj_name):
    """
    Task 3: Convert AST data to Neo4j Cypher queries using Gemini
    Receives result from parse task as first argument
    """
    try:
        logger.info(f"Starting Cypher generation for project: {proj_name}")
        
        # Extract parsed data from parse_result if it's a dict
        parsed_data = parse_result.get("data", []) if isinstance(parse_result, dict) else parse_result
        
        cypher_statements = generate_cypher_from_ast(proj_name, parsed_data)
        
        logger.info(f"Cypher generation complete for {proj_name}")
        
        return {
            "status": "success",
            "project": proj_name,
            "cypher_statements": cypher_statements,
            "message": "Cypher statements generated successfully"
        }
    
    except Exception as e:
        logger.error(f"Cypher generation failed: {str(e)}")
        raise


@shared_task(bind=True, name='tasks.build_knowledge_graph')
def build_knowledge_graph(self, cypher_result, proj_name):
    """
    Task 4: Execute Cypher queries to build Neo4j knowledge graph
    Receives result from generate_cypher task as first argument
    """
    try:
        logger.info(f"Starting knowledge graph build for project: {proj_name}")
        
        # Extract cypher statements from cypher_result if it's a dict
        cypher_statements = cypher_result.get("cypher_statements", []) if isinstance(cypher_result, dict) else cypher_result
        
        if not cypher_statements:
            logger.warning(f"No Cypher statements to execute for {proj_name}")
            return {
                "status": "success",
                "project": proj_name,
                "message": "No Cypher statements to execute",
                "statements_executed": 0
            }
        
        statements_executed = 0
        
        with driver.session() as session:
            for statement in cypher_statements:
                if statement.strip():
                    try:
                        session.run(statement)
                        statements_executed += 1
                    except Exception as e:
                        logger.warning(f"Failed to execute statement: {str(e)}")
                        continue
        
        logger.info(f"Knowledge graph build complete: {statements_executed} statements executed for {proj_name}")
        
        return {
            "status": "success",
            "project": proj_name,
            "statements_executed": statements_executed,
            "message": f"Knowledge graph built with {statements_executed} statements"
        }
    
    except Exception as e:
        logger.error(f"Knowledge graph build failed: {str(e)}")
        raise


@shared_task(bind=True, name='tasks.generate_documentation')
def generate_documentation_task(self, kg_result, proj_name):
    """
    Task 5: Generate README.md documentation from knowledge graph
    Receives result from build_knowledge_graph task as first argument
    Saves documentation to both file and database
    """
    try:
        logger.info(f"Starting documentation generation for project: {proj_name}")
        
        documentation = generate_docs(proj_name)
        
        # Save documentation to file
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_path = os.path.join(BASE_DIR, "UserRepos", proj_name, "GENERATED_README.md")
        
        os.makedirs(os.path.dirname(docs_path), exist_ok=True)
        
        with open(docs_path, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        # Save documentation to Supabase database
        repo_url = user_repo_db[proj_name]["repo_url"] if proj_name in user_repo_db else None
        
        try:
            save_doc_result = save_documentation(proj_name, documentation, repo_url)
            logger.info(f"Documentation saved to database for {proj_name}")
        except Exception as db_error:
            logger.warning(f"Failed to save documentation to database: {str(db_error)}. Continuing with file storage.")
        
        logger.info(f"Documentation generated and saved for {proj_name}")
        
        return {
            "status": "success",
            "project": proj_name,
            "documentation_path": docs_path,
            "documentation": documentation,
            "message": "Documentation generated and stored successfully"
        }
    
    except Exception as e:
        logger.error(f"Documentation generation failed: {str(e)}")
        raise



@shared_task(bind=True, name='tasks.process_repository_pipeline')
def process_repository_pipeline(self, proj_name, repo_url, branch, github_token):
    """
    Task 6: Orchestrator task that chains all pipeline steps
    Executes: Clone → Parse → Cypher → Build KG → Generate Docs
    Returns task chain immediately without blocking
    """
    try:
        logger.info(f"Starting complete pipeline for project: {proj_name}")
        
        # Create task chain (non-blocking async execution)
        pipeline = chain(
            clone_repository.s(proj_name, repo_url, branch, github_token),
            parse_repository.s(proj_name),
            generate_cypher.s(proj_name),
            build_knowledge_graph.s(proj_name),
            generate_documentation_task.s(proj_name)
        )
        
        # Execute chain asynchronously
        result = pipeline.apply_async()
        
        logger.info(f"Pipeline chain started with task id: {result.id}")
        
        return {
            "status": "pipeline_started",
            "chain_task_id": result.id,
            "project": proj_name,
            "message": "Pipeline executing asynchronously"
        }
        
    except Exception as e:
        logger.error(f"Pipeline orchestration failed: {str(e)}")
        return {
            "status": "failed",
            "project": proj_name,
            "error": str(e)
        }


@shared_task(bind=True, name='tasks.cleanup_project')
def cleanup_project(self, proj_name):
    """
    Cleanup task to remove project from database and disk if needed
    """
    try:
        logger.info(f"Cleaning up project: {proj_name}")
        
        if proj_name in user_repo_db:
            path = user_repo_db[proj_name]["local_path"]
            if os.path.exists(path):
                shutil.rmtree(path)
                logger.info(f"Removed directory: {path}")
            del user_repo_db[proj_name]
        
        return {
            "status": "success",
            "project": proj_name,
            "message": f"Project {proj_name} cleaned up"
        }
    
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise

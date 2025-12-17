from google import genai
import shutil
import os
from api.api_routes import parse_repo as ast_parsed_data,RepoNameRequest
import json
from fastapi import APIRouter
from db.neo4j_connect import driver
from dotenv import load_dotenv
from db.data import user_repo_db
load_dotenv()

router=APIRouter()
apiKey=os.getenv("gemini_api_key")
client=genai.Client(api_key=apiKey)

# projectName="interviewAI"

# reqObj=RepoNameRequest(proj_name=projectName)



@router.post("/cypher")
def showCyphertext(request:RepoNameRequest):
     projectName = request.proj_name

     reqObj = RepoNameRequest(proj_name=projectName)

     parsed_output=ast_parsed_data(reqObj)
     ast_json=parsed_output["data"]

     system_prompt = f"""
You are an expert in Neo4j Cypher generation.

Your task is to convert the provided AST JSON into Neo4j Cypher queries using the rules below.

RULES:
1. Output only Cypher queries — no explanations, no markdown, no comments.
2. Use ONLY MERGE statements. Never use CREATE.
3. Every node MUST include a 'project' property set to the project name.
4. Every relationship MUST include a 'project' property set to the project name.
5. For each file, generate a (:File) node with filePath and project.
6. For each class, generate a (:Class) node with className, filePath, and project.
7. For each method, generate a (:Method) node with methodName, parentClass, filePath, and project.
8. Use ONLY these relationships (each must also include {{project: '{projectName}'}}):
     (File)-[:CONTAINS_CLASS {{project: '{projectName}'}}]->(Class)
     (File)-[:CONTAINS_METHOD {{project: '{projectName}'}}]->(Method)
     (Class)-[:HAS_METHOD {{project: '{projectName}'}}]->(Method)
     (Method)-[:CALLS {{project: '{projectName}'}}]->(Method)
9. Every Cypher statement must be separated by a newline.
10. Do NOT wrap the output. Do NOT add any commentary. Output pure Cypher only.

PROJECT = {projectName}
AST_JSON = {json.dumps(ast_json)}
"""


     response=client.models.generate_content(
     model="gemini-2.5-flash", contents=system_prompt
     )
     cypher_text = response.candidates[0].content.parts[0].text.strip()
     print(cypher_text)
     with driver.session() as session:
          for query in cypher_text.split("\n"):
               if query:
                    session.run(query=query)

     # Cleanup: Delete local repo and remove from in-memory DB
     repo_path = user_repo_db[projectName]["local_path"]
     try:
            print("Trying to delete:", repo_path)

            import stat
            def remove_readonly(func, path, excinfo):
                os.chmod(path, stat.S_IWRITE)
                func(path)

            shutil.rmtree(repo_path, onerror=remove_readonly)
            print(f"[Cleanup] Deleted local repo → {repo_path}")

     except Exception as e:
          print(f"[Cleanup Error] Could not delete repo: {e}")

    # Remove from in-memory DB
     if projectName in user_repo_db:
        del user_repo_db[projectName]
        print(f"[Cleanup] Removed {projectName} from in-memory DB")

     return {"cypher": cypher_text}


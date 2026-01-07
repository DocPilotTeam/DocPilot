from google import genai
import shutil
import os
from backend.api.api_routes import parse_repo as ast_parsed_data,RepoNameRequest
import json
from fastapi import APIRouter
from backend.db.neo4j_connect import driver
from dotenv import load_dotenv
from backend.db.data import user_repo_db
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

     system_prompt =  f"""
You are an expert Neo4j Cypher generator.

Your task is to convert the provided AST JSON into Neo4j Cypher statements
that strictly follow the schema and rules below.

IMPORTANT RULES (DO NOT VIOLATE):
1. Output ONLY Cypher statements.
2. No explanations, no markdown, no comments.
3. Use ONLY MERGE statements. Never use CREATE.
4. Every node MUST include a property: project = "{projectName}".
5. Every relationship MUST include a property: project = "{projectName}".
6. Do NOT invent property names. Use EXACT names only.

========================
NODE SCHEMA (STRICT)
========================

(:File)
  - filePath
  - project

(:Class)
  - name
  - filePath
  - project

(:Method)
  - name
  - parentClass
  - filePath
  - project

========================
RELATIONSHIPS (STRICT)
========================

(File)-[:CONTAINS_CLASS {{project: "{projectName}"}}]->(Class)
(File)-[:CONTAINS_METHOD {{project: "{projectName}"}}]->(Method)
(Class)-[:HAS_METHOD {{project: "{projectName}"}}]->(Method)
(Method)-[:CALLS {{project: "{projectName}"}}]->(Method)

========================
GENERATION RULES
========================

- For each file in AST_JSON:
  - MERGE a File node.
- For each class inside the file:
  - MERGE a Class node.
  - MERGE (File)-[:CONTAINS_CLASS]->(Class).
- For each method inside the class:
  - MERGE a Method node.
  - MERGE (Class)-[:HAS_METHOD]->(Method).
  - MERGE (File)-[:CONTAINS_METHOD]->(Method).
- For each method call:
  - MERGE (callerMethod)-[:CALLS]->(calledMethod).

OTHER RULES:
- Every Cypher statement MUST be on a new line.
- Do NOT output empty lines.
- Do NOT output any text outside Cypher.
- Do NOT wrap the output.

PROJECT = "{projectName}"
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


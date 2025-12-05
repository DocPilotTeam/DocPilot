from google import genai
import os
from api.api_routes import parse_repo as ast_parsed_data,RepoNameRequest
import json
from fastapi import APIRouter

router=APIRouter()
apiKey=os.getenv("gemini_api_key")
client=genai.Client(api_key="AIzaSyCp_2htDDWJk-3ZtLrcyqp64Xy5FabiFhY")

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

Your job:
Convert the AST JSON input into Neo4j Cypher queries following the rules below.

RULES:
1. Only output Cypher queries. No explanation, no markdown, no comments.
2. Use ONLY MERGE statements. Never use CREATE.
3. Always include project name in every node and relationship.
4. For each file, create a (:File) node.
5. For each class, create a (:Class) node with its filePath and project.
6. For each method, create a (:Method) node with name, parentClass, filePath, and project.
7. Relationships must use:
     (File)-[:CONTAINS_CLASS]->(Class)
     (File)-[:CONTAINS_METHOD]->(Method)
     (Class)-[:HAS_METHOD]->(Method)
     (Method)-[:CALLS]->(Method)
8. Each Cypher statement must be separated by a newline.
9. Do NOT wrap the output, do NOT add any commentary. Pure Cypher only.

PROJECT = {projectName}
AST_JSON = {json.dumps(ast_json)}
"""
     response=client.models.generate_content(
     model="gemini-2.5-flash", contents=system_prompt
     )
     cypher_text=cypher_text = response.candidates[0].content.parts[0].text.strip()
     print(cypher_text)
     return {"cypher": cypher_text}


from openai import OpenAI
from dotenv import load_dotenv
from backend.agents.kg_builder.Kg_reader import dataRetrive as kg_dataRetrive
import os
import re


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def  generate_docs(projName:str):
    data=kg_dataRetrive(projName)
    prompt=f"""
You are a senior software engineer and technical documentation expert.

Your task is to generate a CLEAN, PROFESSIONAL, and FRAMEWORK-AGNOSTIC
README.md file using the provided knowledge graph data extracted from source code.

STRICT RULES:
1. Output ONLY valid GitHub-flavored Markdown.
2. Do NOT mention specific programming languages or frameworks explicitly.
3. Do NOT include raw AST data, internal IDs, or database-specific details.
4. Use clean, relative file paths (remove repository root prefixes).
5. Do NOT list getters/setters or trivial utility methods.
6. Summarize functionality based on architectural roles and behavior.
7. Keep content concise, readable, and suitable for open-source repositories.

README STRUCTURE (MUST FOLLOW EXACTLY):

# {projName}

## Overview
Describe the purpose of the project in 2–3 sentences, focusing on functionality.

## Architecture Overview
Explain the high-level architectural pattern and separation of concerns.

## Project Structure
Describe major directories and their responsibilities without listing every file.

## Core Components
Summarize the responsibilities of key components:
- Entry point / bootstrap module
- Controllers / handlers
- Services / business logic layer
- Data models
- Persistence / repositories
- Test modules

## Application Flow
Explain how a typical request or operation moves through the system.

## Running the Project
Provide generic, stack-agnostic steps to run the application.

## Testing
Describe how tests are organized and their purpose.

## Notes
Include any important architectural or design observations.


INPUT DATA (DO NOT REPEAT THIS IN OUTPUT):
{data}

Now generate the documentation.
"""
    result=client.chat.completions.create(
    model="tngtech/deepseek-r1t-chimera:free",
    messages=[
        {"role":"user","content":prompt}
    ],
    extra_body={"reasoning":{"enabled":True}}


    )
    content= result.choices[0].message.content

    clean_content=re.sub(r'^```markdown\n|```$', '', content, flags=re.MULTILINE).strip()

    clean_content=clean_content.replace("\\n","\n")

    print(clean_content)

    return clean_content





# print(kg_dataRetrive("emp"))

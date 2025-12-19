from openai import OpenAI
from dotenv import load_dotenv
from backend.agents.kg_builder.Kg_reader import dataRetrive as kg_dataRetrive
import os


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def  generate_docs(projName:str):
    data=kg_dataRetrive(projName)
    prompt=f"""
You are a senior software engineer and technical writer.

Your task is to generate **high-quality project documentation** in **Markdown (.md)** format
using ONLY the provided structured knowledge graph data.

STRICT RULES:
1. Use ONLY the given data. Do NOT assume or invent anything.
2. Output valid Markdown only.
3. Use clear headings, bullet points, and code-style formatting.
4. Follow the structure below exactly.
5. Be concise but complete.

DOCUMENT STRUCTURE:

# {projName} – Project Documentation

## Project Overview
Briefly describe what this project does based on class and method names.

## Code Structure Overview
Explain how the project is organized at a high level.

## Files and Components
For each file:
- File path
- Classes inside the file
- Methods inside each class with short explanations inferred from method names

## Key Classes Summary
List important classes and their responsibilities.

## Method Summary
Summarize important methods and what they do.

INPUT DATA (DO NOT REPEAT THIS IN OUTPUT):
{data}

Now generate the documentation.
"""
    result=client.chat.completions.create(
    model="allenai/olmo-3.1-32b-think:free",
    messages=[
        {"role":"user","content":prompt}
    ],
    extra_body={"reasoning":{"enabled":True}}


    )
    return result.choices[0].message.content



    print(result.choices[0].message.content)

# print(kg_dataRetrive("emp"))

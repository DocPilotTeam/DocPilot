from openai import OpenAI
from dotenv import load_dotenv
from backend.agents.kg_builder.Kg_reader import dataRetrive as kg_dataRetrive
import os


load_dotenv()

client = OpenAI(
    api_key="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",
    base_url="https://opencdrouter.ai/api/v1"
)

result=client.chat.completions.create(
    model="allenai/olmo-3.1-32b-think:free",
    messages=[
        {"role":"user","content":"Hello, how are you? give a short answer."}
    ],
    extra_body={"reasoning":{"enabled":True}}
)

print(result.choices[0].message.content)

print(kg_dataRetrive("emp"))

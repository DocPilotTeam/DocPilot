import json
import os
from openai import OpenAI
from .base_parser import BaseParser
from dotenv import load_dotenv

load_dotenv()

MODEL = "meta/llama-3.1-8b-instruct"  # example NVIDIA-supported model

class LLMFallbackParser(BaseParser):

    def __init__(self):
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY is missing in .env")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )

    def parse_file(self, file_path: str, language: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        prompt = f"""
        You are an expert static code analyzer.

        Analyze the provided {language} source code and extract structured information.

        Return ONLY valid JSON with this schema:
        {{
        "packages": [],
        "file_structure": [],
        "classes": [],
        "functions": [],
        "imports": [],
        "api_endpoints": []
        "interfaces": []
        }}

        Code:
        {code}
        """

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"raw_output": content}

        return {
            "status": "success",
            "file": file_path,
            "language": language,
            "parsed": parsed
        }

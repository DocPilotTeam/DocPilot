import json
import openai
from .base_parser import BaseParser

MODEL = "gpt-4o-mini"

class LLMFallbackParser(BaseParser):

    def __init__(self, llm_client=None):
        self.client = llm_client or openai

    def parse_file(self, file_path: str, language: str) -> dict:

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        prompt = f"""
        You are an expert code analyzer. Extract the following
        from the {language} code below:

        - classes
        - functions/methods
        - imports/dependencies
        - API endpoints (if any)
        - summary: a short description of the file's purpose

        Return ONLY a valid JSON object.

        Code:
        {code}
        """

        response = self.client.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response["choices"][0]["message"]["content"]

        try:
            parsed = json.loads(content)
        except:
            parsed = {"raw_output": content}

        return {
            "file": file_path,
            "language": language,
            "parsed": parsed
        }

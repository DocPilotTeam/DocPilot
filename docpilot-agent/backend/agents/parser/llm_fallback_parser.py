import json
import os
from google import genai
from .base_parser import BaseParser
from dotenv import load_dotenv
load_dotenv()

MODEL = "gemini-2.5-flash"
class LLMFallbackParser(BaseParser):

    def __init__(self):
        api_key = os.getenv("gemini_api_key")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing. Set the environment variable first.")
        self.client = genai.Client(api_key=api_key)

    def parse_file(self, file_path: str, language: str) -> dict:

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        prompt = f"""
        You are an expert static code analyzer.

        Analyze the provided {language} source code and extract structured information.

        Return ONLY valid JSON with:
        - classes: []
        - functions: []
        - imports: []
        - api_endpoints: []
        - summary: ""

        Code:
        {code}
        """

        response = self.client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        content = response.candidates[0].content.parts[0].text

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

import json
import os
import re
import traceback
from typing import Optional
from openai import OpenAI
from .base_parser import BaseParser
from dotenv import load_dotenv

load_dotenv()

MODEL = "gpt-5-nano"  # Efficient model for parsing
MAX_CODE_LENGTH = 10000  # Limit code sent to LLM for efficiency
class LLMFallbackParser(BaseParser):
    """
    Efficient fallback parser that uses OpenAI's GPT-4o-mini for parsing unknown languages,
    with optimized heuristic fallback when LLM is unavailable.

    Features:
    - Uses OPENAI_API_KEY for authentication
    - Limits code input to 10k characters for efficiency
    - Structured JSON prompts for consistent parsing
    - Pre-compiled regexes in heuristic mode
    - Supports wide range of programming languages

    Usage: parse_file(file_path, language)
      - language: a best-effort string (e.g., 'elixir', 'haskell', ...).
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY_LLM_PARSER")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    # ------------------ Heuristic parser ------------------
    # A simple regex-based parser for basic structure extraction when LLM is unavailable.
    def _heuristic_parse(self, code: str, language: str, file_path: str) -> dict:

        # imports/includes (several language patterns)
        imports = []
        for pat in [r"^\s*import\s+([\w\.\*{}]+)", r"^\s*from\s+([\w\.]+)\s+import", r"^\s*require\s*\(?[\'\"]?([\w\-/@\.]+)", r"^\s*#include\s+[<\"]([^>\"]+)[>\"]", r"^\s*using\s+([\w\.]+)"]:
            imports += re.findall(pat, code, re.M)
        imports = list(dict.fromkeys([i.strip() for i in imports if i]))

        # classes / structs / interfaces
        classes = list(dict.fromkeys(re.findall(r"^\s*(?:class|struct|interface|module)\s+([A-Z][A-Za-z0-9_]+)", code, re.M)))

        # functions (common patterns)
        functions = []
        for m in re.finditer(r"^\s*(?:def|function|fun|fn|pub\s+fn|static\s+func|func)\s+([a-zA-Z0-9_<>:\.\-]+)\s*\(([^)]*)\)", code, re.M):
            name = m.group(1)
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            functions.append({"name": name, "params": params})

        # simple method/selector patterns (e.g., Objective-C)
        objc_methods = re.findall(r"[+-]\s*\([^\)]*\)\s*([a-zA-Z0-9_:\s]+)", code)
        for sig in objc_methods:
            functions.append({"name": sig.strip(), "params": []})

        # endpoints / routes (heuristic)
        endpoints = []
        for m in re.finditer(r"\.(get|post|put|delete|patch|route)\s*\(\s*['\"]([^'\"]+)['\"]", code, re.I):
            endpoints.append({"method": m.group(1).upper(), "path": m.group(2)})

        # constants
        constants = list(dict.fromkeys(re.findall(r"^\s*(?:const|#define|val|let|var|CONST)\s+([A-Z0-9_][A-Z0-9_\-]*)", code, re.M)))

        return {
            "file": file_path,
            "language": language,
            "heuristic": {
                "imports": imports,
                "classes": classes,
                "functions": functions,
                "endpoints": endpoints,
                "constants": constants
            }
        }

    # ------------------ Main parse ------------------
    def parse_file(self, file_path: str, language: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # If LLM client is not configured, use heuristic immediately
        if not self.client:
            return {"status": "heuristic", **self._heuristic_parse(code, language, file_path)}

        # Limit code length for efficiency
        if len(code) > MAX_CODE_LENGTH:
            code = code[:MAX_CODE_LENGTH] + "\n... [truncated for efficiency]"

        # Build optimized prompt for the LLM
        prompt = f"""Analyze this {language} code file and extract structured information.

Return ONLY valid JSON with these keys (use empty arrays/objects if none found):
{{
  "imports": ["list", "of", "imports"],
  "classes": ["ClassName1", "ClassName2"],
  "functions": [{{"name": "func1", "params": ["param1", "param2"]}}],
  "interfaces": ["Interface1"],
  "constants": ["CONST1", "CONST2"],
  "api_endpoints": [{{"method": "GET", "path": "/api/route"}}],
  "packages": ["package1", "package2"]
}}

Code:
{code}
"""

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1000  # Limit response length for efficiency
            )

            content = response.choices[0].message.content

            # Try to parse JSON directly
            try:
                parsed = json.loads(content)
                return {
                    "status": "llm",
                    "file": file_path,
                    "language": language,
                    "imports": parsed.get("imports", []),
                    "classes": parsed.get("classes", []),
                    "functions": parsed.get("functions", []),
                    "interfaces": parsed.get("interfaces", []),
                    "constants": parsed.get("constants", []),
                    "api_endpoints": parsed.get("api_endpoints", []),
                    "packages": parsed.get("packages", [])
                }
            except json.JSONDecodeError:
                # Attempt to extract a JSON blob from the returned text
                m = re.search(r"(\{[\s\S]*\})", content)
                if m:
                    blob = m.group(1)
                    try:
                        parsed = json.loads(blob)
                        return {
                            "status": "llm",
                            "file": file_path,
                            "language": language,
                            "imports": parsed.get("imports", []),
                            "classes": parsed.get("classes", []),
                            "functions": parsed.get("functions", []),
                            "interfaces": parsed.get("interfaces", []),
                            "constants": parsed.get("constants", []),
                            "api_endpoints": parsed.get("api_endpoints", []),
                            "packages": parsed.get("packages", [])
                        }
                    except json.JSONDecodeError:
                        pass

                # If JSON can't be recovered, include raw LLM output and fallback
                return {
                    "status": "llm_error_fallback",
                    "file": file_path,
                    "language": language,
                    "raw_llm": content,
                    **self._heuristic_parse(code, language, file_path)
                }

        except Exception as e:
            # On any LLM error, fallback to heuristic parser and include error info
            return {
                "status": "llm_exception_fallback",
                "file": file_path,
                "language": language,
                "error": str(e),
                "traceback": traceback.format_exc(),
                **self._heuristic_parse(code, language, file_path)
            }


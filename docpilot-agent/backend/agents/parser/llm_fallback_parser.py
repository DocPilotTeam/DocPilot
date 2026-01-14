import json
import os
import re
import traceback
from typing import Optional
from openai import OpenAI
from .base_parser import BaseParser
from dotenv import load_dotenv

load_dotenv()

MODEL="gemini-2.5-flash"
class LLMFallbackParser(BaseParser):
    """
    Fallback parser that uses an LLM when available, otherwise uses a local
    heuristic parser to extract basic structure from arbitrary source files.

    Usage: parse_file(file_path, language)
      - language: a best-effort string (e.g., 'elixir', 'haskell', ...).
    """

    def __init__(self):
        api_key = os.getenv("gemini_api_key")
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            )
        else:
            # don't raise here — prefer graceful heuristic fallback
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
        constants = list(dict.fromkeys(re.findall(r"^\s*(?:const|#define|val|let)\s+([A-Z0-9_][A-Z0-9_\-]*)", code, re.M)))

        return {
            "file": file_path,
            "language": language,
            "heuristic": {
                "imports": imports,
                "classes": classes,
                "functions": functions,
                "objc_methods": [s.strip() for s in objc_methods],
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

        # Build prompt for the LLM
        prompt = f"""
You are an expert static code analyzer. Given source code in an unknown language ({language}), extract meaningful structured information.
Return ONLY valid JSON with keys (optional when absent):
- packages (list), file_structure (list), classes (list), functions (list), imports (list), api_endpoints (list), interfaces (list), comments (object)
If you cannot analyze precisely, return a best-effort JSON; do not include extraneous text.

Code:
{code}
"""

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            content = response.choices[0].message.content

            # Try to parse JSON directly
            try:
                parsed = json.loads(content)
                return {"status": "llm", "file": file_path, "language": language, "parsed": parsed}
            except json.JSONDecodeError:
                # Attempt to extract a JSON blob from the returned text
                m = re.search(r"(\{[\s\S]*\})", content)
                if m:
                    blob = m.group(1)
                    try:
                        parsed = json.loads(blob)
                        return {"status": "llm", "file": file_path, "language": language, "parsed": parsed}
                    except json.JSONDecodeError:
                        # fall through to heuristic
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


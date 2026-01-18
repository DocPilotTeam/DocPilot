import re
from .base_parser import BaseParser

class RubyParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        imports = re.findall(r"^\s*(?:require|require_relative|load)\s+[\"']([^\"']+)[\"']", code, re.M)
        classes = re.findall(r"^\s*class\s+([A-Z]\w+)", code, re.M)
        modules = re.findall(r"^\s*module\s+([A-Z]\w+)", code, re.M)
        methods = []
        for m in re.finditer(r"^\s*def\s+([a-zA-Z0-9_!?=]+)\s*(\([^\)]*\))?", code, re.M):
            params_raw = m.group(2) or ""
            params = [p.strip() for p in params_raw.strip('()').split(',') if p.strip()]
            methods.append({"name": m.group(1), "params": params})

        comments = re.findall(r"#.*", code)
        docblocks = re.findall(r"/\*\*[\s\S]*?\*/", code)

        return {
            "file": file_path,
            "language": "ruby",
            "imports": imports,
            "modules": modules,
            "classes": classes,
            "functions": methods,
            "comments": {"single_line": comments, "docblocks": docblocks}
        }

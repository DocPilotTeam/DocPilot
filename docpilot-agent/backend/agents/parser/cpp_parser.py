import re
from .base_parser import BaseParser

class CppParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        includes = re.findall(r"^\s*#include\s+[<\"]([^>\"]+)[>\"]", code, re.M)
        namespaces = re.findall(r"^\s*namespace\s+([a-zA-Z0-9_]+)", code, re.M)
        classes = re.findall(r"^\s*class\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        structs = re.findall(r"^\s*struct\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        functions = []
        for m in re.finditer(r"^\s*([\w:\*\&<>~]+)\s+([a-zA-Z_][a-zA-Z0-9_:\.]*)\s*\(([^;{)]*)\)\s*(?:;|\{)", code, re.M):
            ret = m.group(1).strip()
            name = m.group(2).strip()
            params = [p.strip() for p in m.group(3).split(',') if p.strip()]
            functions.append({"name": name, "return": ret, "params": params})

        macros = re.findall(r"^\s*#define\s+([A-Z0-9_]+)", code, re.M)
        comments = re.findall(r"//.*", code)
        block_comments = re.findall(r"/\*[\s\S]*?\*/", code)

        return {
            "file": file_path,
            "language": "cpp",
            "includes": includes,
            "namespaces": namespaces,
            "classes": classes,
            "structs": structs,
            "functions": functions,
            "macros": macros,
            "comments": {"single_line": comments, "block": block_comments}
        }

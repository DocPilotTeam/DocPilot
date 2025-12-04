import re
from .base_parser import BaseParser

class JavaParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        classes = re.findall(r'\bclass\s+(\w+)', code)
        interfaces = re.findall(r'\binterface\s+(\w+)', code)
        methods = re.findall(
            r'(public|private|protected)\s+[\w<>]+\s+(\w+)\s*\(',
            code
        )
        method_names = [m[1] for m in methods]
        imports = re.findall(r'import\s+([\w\.]+);', code)

        return {
            "file": file_path,
            "language": "java",
            "classes": classes,
            "interfaces": interfaces,
            "methods": method_names,
            "imports": imports
        }

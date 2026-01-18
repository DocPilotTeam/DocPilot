import re
from .base_parser import BaseParser

class CSharpParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        usings = re.findall(r"^\s*using\s+([A-Za-z0-9_\.]+)\s*;", code, re.M)
        namespaces = re.findall(r"^\s*namespace\s+([A-Za-z0-9_.]+)", code, re.M)
        classes = re.findall(r"^\s*(?:public\s+|internal\s+|private\s+)?(?:partial\s+)?class\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        interfaces = re.findall(r"^\s*interface\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        functions = []
        for m in re.finditer(r"^\s*(?:public|private|internal|protected|static)\s+[\w<>\[\]]+\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)", code, re.M):
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            functions.append({"name": m.group(1), "params": params})

        comments = re.findall(r"//.*", code)
        xml_comments = re.findall(r"///.*", code)

        return {
            "file": file_path,
            "language": "csharp",
            "usings": usings,
            "namespaces": namespaces,
            "classes": classes,
            "interfaces": interfaces,
            "functions": functions,
            "comments": {"single_line": comments, "xml": xml_comments}
        }

import re
from .base_parser import BaseParser

class KotlinParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        imports = re.findall(r"^\s*import\s+([\w\.]+)", code, re.M)
        packages = re.findall(r"^\s*package\s+([\w\.]+)", code, re.M)
        classes = re.findall(r"^\s*(?:public\s+|internal\s+|private\s+)?(?:data\s+)?class\s+([A-Z]\w+)", code, re.M)
        objects = re.findall(r"^\s*object\s+([A-Z]\w+)", code, re.M)
        functions = []
        for m in re.finditer(r"^\s*(?:public\s+|private\s+|internal\s+)?fun\s+([a-zA-Z0-9_<>,?]+)\s*\(([^)]*)\)", code, re.M):
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            functions.append({"name": m.group(1), "params": params})

        comments = re.findall(r"//.*", code)
        ktdoc = re.findall(r"/\*\*[\s\S]*?\*/", code)

        return {
            "file": file_path,
            "language": "kotlin",
            "package": packages[0] if packages else None,
            "imports": imports,
            "classes": classes,
            "objects": objects,
            "functions": functions,
            "comments": {"single_line": comments, "docblocks": ktdoc}
        }

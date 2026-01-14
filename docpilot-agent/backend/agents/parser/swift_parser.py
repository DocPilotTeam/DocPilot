import re
from .base_parser import BaseParser

class SwiftParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        imports = re.findall(r"^\s*import\s+([A-Za-z0-9_\.]+)", code, re.M)
        classes = re.findall(r"^\s*(?:public\s+|internal\s+|private\s+)?class\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        structs = re.findall(r"^\s*struct\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        enums = re.findall(r"^\s*enum\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        functions = []
        for m in re.finditer(r"^\s*(?:public\s+|private\s+|internal\s+)?func\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)", code, re.M):
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            functions.append({"name": m.group(1), "params": params})

        comments = re.findall(r"//.*", code)
        docblocks = re.findall(r"/\*\*[\s\S]*?\*/", code)

        return {
            "file": file_path,
            "language": "swift",
            "imports": imports,
            "classes": classes,
            "structs": structs,
            "enums": enums,
            "functions": functions,
            "comments": {"single_line": comments, "docblocks": docblocks}
        }

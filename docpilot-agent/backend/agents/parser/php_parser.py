import re
from .base_parser import BaseParser

class PHPParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # strip opening <?php tag if present
        code_body = re.sub(r"^\s*<\?php", "", code, flags=re.I)

        namespaces = re.findall(r"^\s*namespace\s+([A-Za-z0-9_\\]+);", code_body, re.M)
        uses = re.findall(r"^\s*use\s+([A-Za-z0-9_\\]+);", code_body, re.M)
        classes = re.findall(r"^\s*(?:abstract\s+|final\s+)?class\s+([A-Z][A-Za-z0-9_]+)", code_body, re.M)
        functions = []
        for m in re.finditer(r"^\s*function\s+&?\s*([a-zA-Z0-9_]+)\s*\(([^)]*)\)", code_body, re.M):
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            functions.append({"name": m.group(1), "params": params})

        docblocks = re.findall(r"/\*\*[\s\S]*?\*/", code_body)
        comments = re.findall(r"//.*", code_body)

        return {
            "file": file_path,
            "language": "php",
            "namespaces": namespaces,
            "uses": uses,
            "classes": classes,
            "functions": functions,
            "comments": {"single_line": comments, "docblocks": docblocks}
        }

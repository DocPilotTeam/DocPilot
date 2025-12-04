import re
from .base_parser import BaseParser

class JSParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        functions = re.findall(r'function\s+(\w+)', code)
        arrow_functions = re.findall(r'(\w+)\s*=\s*\([^)]*\)\s*=>', code)
        classes = re.findall(r'class\s+(\w+)', code)
        imports = re.findall(r'import\s+.*\s+from\s+[\'"](.+?)[\'"]', code)

        # Express.js API detection
        routes = re.findall(
            r'app\.(get|post|put|delete)\(\s*[\'"]([^\'"]+)[\'"]',
            code
        )

        return {
            "file": file_path,
            "language": "javascript",
            "classes": classes,
            "functions": list(set(functions + arrow_functions)),
            "imports": imports,
            "routes": routes
        }

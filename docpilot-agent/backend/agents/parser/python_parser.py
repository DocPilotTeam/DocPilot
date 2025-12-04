import ast
from .base_parser import BaseParser

class PythonParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            tree = ast.parse(code)
        except Exception as e:
            return {"file": file_path, "language": "python", "error": str(e)}

        classes = []
        functions = []
        imports = []

        for node in ast.walk(tree):

            if isinstance(node, ast.ClassDef):
                classes.append(node.name)

            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)

            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)

            if isinstance(node, ast.ImportFrom):
                imports.append(node.module)

        return {
            "file": file_path,
            "language": "python",
            "classes": classes,
            "functions": functions,
            "imports": imports
        }

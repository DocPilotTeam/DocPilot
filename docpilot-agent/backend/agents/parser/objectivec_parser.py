import re
from .base_parser import BaseParser

class ObjectiveCParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        imports = re.findall(r"^\s*#import\s+[<\"]([^>\"]+)[>\"]", code, re.M)
        includes = re.findall(r"^\s*#include\s+[<\"]([^>\"]+)[>\"]", code, re.M)
        interfaces = re.findall(r"^\s*@interface\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        implementations = re.findall(r"^\s*@implementation\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        methods = []
        for m in re.finditer(r"(\+|-)\s*\(.*?\)\s*([a-zA-Z0-9_:\s]+)\{", code):
            sig = m.group(0).strip()
            methods.append({"signature": sig})

        comments = re.findall(r"//.*", code)
        block_comments = re.findall(r"/\*[\s\S]*?\*/", code)

        return {
            "file": file_path,
            "language": "objectivec",
            "imports": imports,
            "includes": includes,
            "interfaces": interfaces,
            "implementations": implementations,
            "methods": methods,
            "comments": {"single_line": comments, "block": block_comments}
        }

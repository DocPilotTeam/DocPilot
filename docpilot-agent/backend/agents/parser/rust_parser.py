import re
from .base_parser import BaseParser

class RustParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        uses = re.findall(r"^\s*use\s+([^;]+);", code, re.M)
        extern_crates = re.findall(r"^\s*extern\s+crate\s+([\w_]+)", code, re.M)
        structs = re.findall(r"^\s*pub?\s*struct\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        enums = re.findall(r"^\s*pub?\s*enum\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        traits = re.findall(r"^\s*pub?\s*trait\s+([A-Z][A-Za-z0-9_]+)", code, re.M)
        functions = []
        for m in re.finditer(r"^\s*pub?\s*fn\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)", code, re.M):
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            functions.append({"name": m.group(1), "params": params})

        macros = re.findall(r"^\s*macro_rules!\s*([a-zA-Z0-9_]+)", code, re.M)
        comments = re.findall(r"//.*", code)
        block_comments = re.findall(r"/\*[\s\S]*?\*/", code)

        return {
            "file": file_path,
            "language": "rust",
            "uses": uses,
            "extern_crates": extern_crates,
            "structs": structs,
            "enums": enums,
            "traits": traits,
            "functions": functions,
            "macros": macros,
            "comments": {"single_line": comments, "block": block_comments}
        }

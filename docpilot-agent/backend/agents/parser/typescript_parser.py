# parser-agent/typescript_parser.py
import re
from pathlib import Path
from .base_parser import BaseParser

class TypeScriptParser(BaseParser):
    """
    Heuristic TypeScript parser (regex-based).
    Extracts:
     - interfaces
     - type aliases
     - enums
     - classes (with generics)
     - methods (and method decorators like @Get/@Post)
     - imports (including `import type`)
     - exports
     - top-level functions/consts
     - decorators on classes (e.g., @Controller)
    """

    # regex patterns
    RE_INTERFACE = re.compile(r'\binterface\s+([A-Za-z_]\w*)', re.MULTILINE)
    RE_TYPE_ALIAS = re.compile(r'\btype\s+([A-Za-z_]\w*)\s*=', re.MULTILINE)
    RE_ENUM = re.compile(r'\benum\s+([A-Za-z_]\w*)', re.MULTILINE)
    RE_CLASS = re.compile(r'\bclass\s+([A-Za-z_]\w*)(?:\s*<\s*([^>{]+)\s*>)?', re.MULTILINE)
    RE_IMPORT = re.compile(r'import\s+(?:type\s+)?(?:[\s\S]+?)\s+from\s+[\'"](.+?)[\'"]', re.MULTILINE)
    RE_EXPORT = re.compile(r'\bexport\s+(?:default\s+)?(?:class|function|const|let|var|type|interface|enum)\s+([A-Za-z_]\w*)', re.MULTILINE)
    RE_TOP_FUNC = re.compile(r'\bfunction\s+([A-Za-z_]\w*)\s*\(', re.MULTILINE)
    RE_TOP_CONST = re.compile(r'\b(?:const|let|var)\s+([A-Za-z_]\w*)\s*[:=]\s', re.MULTILINE)

    # Decorator detection (NestJS / TS decorators)
    RE_DECORATOR = re.compile(r'@([A-Za-z_]\w*)(?:\((["\']?([^"\')]+)["\']?)\))?', re.MULTILINE)
    # Capture method decorators like @Get('/path') followed by method name
    RE_METHOD_WITH_DECORATOR = re.compile(
        r'@(?P<decorator>(Get|Post|Put|Delete|Patch|All|Head|Options|UseGuards|UseInterceptors|UsePipes|Roles))\s*\(\s*[\'"](?P<path>[^\'"]*)[\'"]\s*\)\s*'  # decorator(path)
        r'(?:public|private|protected)?\s*(?:async\s*)?(?P<name>[A-Za-z_]\w*)\s*\(', re.MULTILINE)

    # For methods without decorator, capture method names inside classes (approx)
    RE_CLASS_METHOD = re.compile(r'(?:public|private|protected)?\s*(?:async\s*)?(?P<name>[A-Za-z_]\w*)\s*\([^)]*\)\s*[:{]', re.MULTILINE)

    def parse_file(self, file_path: str) -> dict:
        path = Path(file_path)
        try:
            raw = path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            return {"file": file_path, "language": "typescript", "error": f"could not read file: {e}"}

        # quick normalize (remove long block comments to reduce false positives)
        code = re.sub(r'/\*[\s\S]*?\*/', '', raw)
        code_no_line_comments = re.sub(r'//.*', '', code)

        interfaces = self.RE_INTERFACE.findall(code_no_line_comments)
        type_aliases = self.RE_TYPE_ALIAS.findall(code_no_line_comments)
        enums = self.RE_ENUM.findall(code_no_line_comments)

        # classes and generics
        classes = []
        for m in self.RE_CLASS.finditer(code_no_line_comments):
            cls_name = m.group(1)
            generics = m.group(2).strip() if m.group(2) else None
            classes.append({"name": cls_name, "generics": generics})

        # imports (unique)
        imports = list(dict.fromkeys(self.RE_IMPORT.findall(code_no_line_comments)))

        # exports
        exports = self.RE_EXPORT.findall(code_no_line_comments)

        # top-level functions and consts (unique)
        functions = list(dict.fromkeys(self.RE_TOP_FUNC.findall(code_no_line_comments)))
        top_consts = list(dict.fromkeys(self.RE_TOP_CONST.findall(code_no_line_comments)))

        # decorators on classes: find class blocks with leading decorators
        class_decorators = []
        # pattern: decorators preceding class declaration (up to 3 decorators)
        for cm in re.finditer(r'((?:@\w+(?:\([^)]*\))?\s*){0,6})\s*(?:export\s+)?class\s+([A-Za-z_]\w*)', code_no_line_comments):
            decorator_block = cm.group(1).strip()
            clsname = cm.group(2)
            if decorator_block:
                decs = self.RE_DECORATOR.findall(decorator_block)
                decs_clean = [{"name": d[0], "arg": d[2] if d[2] else None} for d in decs]
            else:
                decs_clean = []
            class_decorators.append({"class": clsname, "decorators": decs_clean})

        # method-level decorators + routes (NestJS-style)
        routes = []
        for m in self.RE_METHOD_WITH_DECORATOR.finditer(code_no_line_comments):
            dec = m.group('decorator')
            path = m.group('path')
            name = m.group('name')
            routes.append({"decorator": dec, "path": path, "handler": name})

        # general methods inside classes (best-effort)
        # find class bodies and extract method names (simple heuristic)
        class_methods = {}
        for cls in classes:
            # attempt to locate class body by class name
            pattern = r'class\s+' + re.escape(cls["name"]) + r'(?:\s*<[^>]+>)?\s*{([\s\S]*?)}'
            cmatch = re.search(pattern, code_no_line_comments)
            methods = []
            if cmatch:
                body = cmatch.group(1)
                for mm in self.RE_CLASS_METHOD.finditer(body):
                    methods.append(mm.group('name'))
            class_methods[cls["name"]] = list(dict.fromkeys(methods))

        # short summary heuristics
        summary = self._generate_summary(code_no_line_comments)

        result = {
            "file": file_path,
            "language": "typescript",
            "interfaces": interfaces,
            "type_aliases": type_aliases,
            "enums": enums,
            "classes": classes,
            "class_methods": class_methods,
            "imports": imports,
            "exports": exports,
            "functions": functions,
            "top_level_consts": top_consts,
            "class_decorators": class_decorators,
            "routes": routes,
            "summary": summary
        }

        return result

    def _generate_summary(self, code: str) -> str:
        # very small heuristic summary: looks for keywords
        lines = code.splitlines()
        # find first non-empty line with significant token
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            if s.startswith('import'):
                continue
            # return short snippet as summary
            return (s[:200] + '...') if len(s) > 200 else s
        return "TypeScript file (no summary found)."

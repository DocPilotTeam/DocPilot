import re
from .base_parser import BaseParser


class GoParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        return {
            "file": file_path,
            "language": "go",
            "package": self._parse_package(code),
            "imports": self._parse_imports(code),
            "structs": self._parse_structs(code),
            "interfaces": self._parse_interfaces(code),
            "functions": self._parse_functions(code),
            "endpoints": self._parse_endpoints(code),
        }

    # -------------------------
    # Package & Imports
    # -------------------------
    def _parse_package(self, code: str):
        m = re.search(r"^\s*package\s+(\w+)", code, re.MULTILINE)
        return m.group(1) if m else None

    def _parse_imports(self, code: str):
        imports = []
        # single-line imports: import "fmt"
        for m in re.finditer(r"import\s+['\"]([^'\"]+)['\"]", code):
            imports.append({"module": m.group(1), "type": "single"})

        # grouped imports: import ("fmt" "net/http") or import (\n "fmt" \n "x")
        for m in re.finditer(r"import\s*\(([^)]+)\)", code, re.DOTALL):
            group = m.group(1)
            for im in re.finditer(r"['\"]([^'\"]+)['\"]", group):
                imports.append({"module": im.group(1), "type": "group"})

        # aliased imports: alias "module"
        for m in re.finditer(r"(\w+)\s+['\"]([^'\"]+)['\"]", code):
            imports.append({"module": m.group(2), "alias": m.group(1)})

        return imports

    # -------------------------
    # Structs & Interfaces
    # -------------------------
    def _parse_structs(self, code: str):
        results = []
        for m in re.finditer(r"type\s+(?P<name>\w+)\s+struct\s*\{(?P<body>[\s\S]*?)\}", code):
            body = m.group('body').strip()
            fields = []
            for line in body.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    fname = parts[0]
                    ftype = parts[1]
                    tag = None
                    if len(parts) > 2:
                        tag = ' '.join(parts[2:])
                    fields.append({"name": fname, "type": ftype, "tag": tag})
            results.append({"name": m.group('name'), "fields": fields})
        return results

    def _parse_interfaces(self, code: str):
        results = []
        for m in re.finditer(r"type\s+(?P<name>\w+)\s+interface\s*\{(?P<body>[\s\S]*?)\}", code):
            body = m.group('body').strip()
            methods = []
            for line in body.splitlines():
                line = line.strip()
                if line:
                    methods.append(line)
            results.append({"name": m.group('name'), "methods": methods})
        return results

    # -------------------------
    # Functions & Methods
    # -------------------------
    def _parse_functions(self, code: str):
        results = []
        # methods with receiver: func (r *Router) Handle(path string) {}
        method_pat = re.compile(r"func\s*\((?P<recv>[^)]+)\)\s*(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*(?P<returns>\([^)]*\)|[\w\*\.]+)?", re.MULTILINE)
        for m in method_pat.finditer(code):
            results.append({
                "name": m.group('name'),
                "receiver": m.group('recv').strip(),
                "params": [p.strip() for p in m.group('params').split(',') if p.strip()],
                "returns": m.group('returns').strip() if m.group('returns') else None
            })

        # functions without receiver: func Name(params) (returns) {}
        func_pat = re.compile(r"func\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*(?P<returns>\([^)]*\)|[\w\*\.]+)?", re.MULTILINE)
        for m in func_pat.finditer(code):
            # skip those that were caught as methods (they include receiver)
            if re.match(r"func\s*\(", code[m.start()-10:m.start()+5] if m.start() >= 10 else ''):
                continue
            results.append({
                "name": m.group('name'),
                "receiver": None,
                "params": [p.strip() for p in m.group('params').split(',') if p.strip()],
                "returns": m.group('returns').strip() if m.group('returns') else None
            })

        return results
    # -------------------------
    # Endpoints (http handlers - net/http, gorilla/mux, gin)
    # -------------------------
    def _parse_endpoints(self, code: str):
        endpoints = []
        # http.HandleFunc("/path", handler)
        for m in re.finditer(r"\b(\w+)\.HandleFunc\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^\)]+)\)", code):
            endpoints.append({"router": m.group(1), "path": m.group(2), "handler": m.group(3).strip()})

        # router.GET("/path", handler) - gin or gorilla mux with method name
        for m in re.finditer(r"\b(\w+)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^\)]+)\)", code):
            endpoints.append({"router": m.group(1), "method": m.group(2), "path": m.group(3), "handler": m.group(4).strip()})

        # http.Handle("/path", handler) or mux.Handle
        for m in re.finditer(r"\b(\w+)\.Handle\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^\)]+)\)", code):
            endpoints.append({"router": m.group(1), "path": m.group(2), "handler": m.group(3).strip()})

        return endpoints

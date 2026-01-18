import re
from .base_parser import BaseParser


class JavaParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        return {
            "file": file_path,
            "language": "java",
            "package": self._parse_package(code),
            "imports": self._parse_imports(code),
            "annotations": self._parse_annotations(code),
            "classes": self._parse_classes(code),
            "interfaces": self._parse_interfaces(code),
            "enums": self._parse_enums(code),
            "records": self._parse_records(code),
            "fields": self._parse_fields(code),
            "constructors": self._parse_constructors(code),
            "methods": self._parse_methods(code),
            "apis": self._parse_apis(code),
            "comments": self._parse_comments(code),
        }

    # -------------------------
    # Package & Imports
    # -------------------------
    def _parse_package(self, code):
        match = re.search(r'package\s+([\w\.]+)\s*;', code)
        return match.group(1) if match else None

    def _parse_imports(self, code):
        return re.findall(r'import\s+(static\s+)?([\w\.]+)\s*;', code)

    # -------------------------
    # Annotations
    # -------------------------
    def _parse_annotations(self, code):
        return re.findall(r'@\w+(?:\([^)]*\))?', code)

    # -------------------------
    # Classes / Interfaces / Enums / Records
    # -------------------------
    def _parse_classes(self, code):
        return self._parse_types(code, "class")

    def _parse_interfaces(self, code):
        return self._parse_types(code, "interface")

    def _parse_enums(self, code):
        return self._parse_types(code, "enum")

    def _parse_records(self, code):
        return self._parse_types(code, "record")

    def _parse_types(self, code, type_name):
        pattern = rf'''
            ((public|private|protected|abstract|final|static)\s+)*
            {type_name}\s+
            (\w+)
            (?:\s+extends\s+([\w<>.,\s]+))?
            (?:\s+implements\s+([\w<>.,\s]+))?
        '''
        matches = re.finditer(pattern, code, re.VERBOSE)
        results = []

        for m in matches:
            results.append({
                "name": m.group(3),
                "modifiers": m.group(1).strip().split() if m.group(1) else [],
                "extends": m.group(4).split(",") if m.group(4) else [],
                "implements": m.group(5).split(",") if m.group(5) else [],
            })
        return results

    # -------------------------
    # Fields
    # -------------------------
    def _parse_fields(self, code):
        pattern = r'''
            (public|private|protected)?\s*
            (static|final|transient|volatile)?\s*
            ([\w<>[\]]+)\s+
            (\w+)\s*
            (=.*)?;
        '''
        matches = re.finditer(pattern, code, re.VERBOSE)
        fields = []

        for m in matches:
            fields.append({
                "name": m.group(4),
                "type": m.group(3),
                "modifiers": [g for g in m.groups()[:2] if g],
            })
        return fields

    # -------------------------
    # Constructors
    # -------------------------
    def _parse_constructors(self, code):
        pattern = r'''
            (public|private|protected)\s+
            (\w+)\s*
            \(([^)]*)\)
        '''
        matches = re.finditer(pattern, code, re.VERBOSE)
        return [{
            "name": m.group(2),
            "access": m.group(1),
            "parameters": self._parse_parameters(m.group(3))
        } for m in matches]

    # -------------------------
    # Methods
    # -------------------------
    def _parse_methods(self, code):
        pattern = r'''
            (public|private|protected)?\s*
            (static|final|abstract|synchronized)?\s*
            ([\w<>[\]]+)\s+
            (\w+)\s*
            \(([^)]*)\)
            (?:\s+throws\s+([\w.,\s]+))?
        '''
        matches = re.finditer(pattern, code, re.VERBOSE)
        methods = []

        for m in matches:
            methods.append({
                "name": m.group(4),
                "return_type": m.group(3),
                "modifiers": [g for g in m.groups()[:2] if g],
                "parameters": self._parse_parameters(m.group(5)),
                "throws": m.group(6).split(",") if m.group(6) else []
            })
        return methods

    def _parse_parameters(self, params):
        if not params.strip():
            return []
        result = []
        for p in params.split(","):
            parts = p.strip().split()
            if len(parts) >= 2:
                result.append({
                    "type": " ".join(parts[:-1]),
                    "name": parts[-1]
                })
        return result
    
    # -------------------------
    # Comments
    # -------------------------
    def _parse_comments(self, code):
        javadoc = re.findall(r'/\*\*[\s\S]*?\*/', code)
        single_line = re.findall(r'//.*', code)
        return {
            "javadoc": javadoc,
            "single_line": single_line
        }

    # -------------------------
    # APIs (Spring MVC / JAX-RS)
    # -------------------------
    def _parse_apis(self, code):
        """Parse API endpoints (Spring MVC and JAX-RS).
        Returns a list of endpoints with name, http_methods, path, return_type, parameters, annotations."""
        # class-level base paths
        class_bases = {}
        class_ann_pattern = r'@(?P<ann>RequestMapping|Path)\s*(\([^)]*\))?[\s\S]*?class\s+(?P<classname>\w+)'
        for m in re.finditer(class_ann_pattern, code):
            ann_block = m.group(0)
            base_path = self._extract_path_from_annotation(ann_block)
            classname = m.group('classname')
            class_bases[classname] = base_path or ""

        # collect class positions to map methods to classes
        class_positions = [(cm.group(1), cm.start()) for cm in re.finditer(r'class\s+(\w+)', code)]

        # method-level annotations and methods
        method_pattern = r'(?P<annotations>(?:@[A-Za-z0-9_]+\s*(?:\([^)]*\))?\s*)+)\s*(?:public|private|protected)?\s*(?:static|final|synchronized)?\s*([\w<>\[\]]+)\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)'
        apis = []
        for m in re.finditer(method_pattern, code):
            ann_block = m.group('annotations')
            method_name = m.group('name')
            return_type = m.group(3)
            params = m.group('params')
            annotations = re.findall(r'@[\w]+(?:\([^)]*\))?', ann_block)

            # find enclosing class name by position
            method_pos = m.start()
            cls_name = None
            for cname, cpos in class_positions:
                if cpos < method_pos:
                    cls_name = cname
                else:
                    break
            base_path = class_bases.get(cls_name, "")

            # find mapping annotations
            mapping_annos = []
            for ann in annotations:
                name_match = re.match(r'@([A-Za-z0-9_]+)', ann)
                if not name_match:
                    continue
                ann_name = name_match.group(1)

                http_methods = []
                method_path = None

                if ann_name in ("GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping"):
                    http_methods = [ann_name.replace('Mapping', '').upper()]
                    method_path = self._extract_path_from_annotation(ann)
                elif ann_name == 'RequestMapping':
                    method_path = self._extract_path_from_annotation(ann)
                    req_method = self._extract_method_from_requestmapping(ann)
                    if req_method:
                        http_methods = [req_method]
                elif ann_name in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    http_methods = [ann_name]
                    # look for @Path in annotations
                    for a in annotations:
                        if a.startswith('@Path'):
                            method_path = self._extract_path_from_annotation(a)
                elif ann_name == 'Path':
                    method_path = self._extract_path_from_annotation(ann)

                if http_methods or method_path is not None:
                    full_path = self._join_paths(base_path, method_path)
                    apis.append({
                        "name": method_name,
                        "http_methods": http_methods if http_methods else [],
                        "path": full_path,
                        "return_type": return_type,
                        "parameters": self._parse_parameters(params),
                        "annotations": annotations
                    })

        return apis

    def _extract_path_from_annotation(self, ann_str: str):
        # try path=, value=, or a single quoted argument
        m = re.search(r'path\s*=\s*"([^"]+)"', ann_str)
        if not m:
            m = re.search(r'value\s*=\s*"([^"]+)"', ann_str)
        if not m:
            m = re.search(r'\(\s*"([^"]+)"\s*\)', ann_str)
        if not m:
            m = re.search(r'"([^"]+)"', ann_str)
        return m.group(1).strip() if m else None

    def _extract_method_from_requestmapping(self, ann_str: str):
        # look for RequestMethod.X or method = {RequestMethod.X,...}
        m = re.search(r'RequestMethod\.([A-Z_]+)', ann_str)
        if m:
            return m.group(1)
        m = re.search(r'method\s*=\s*\{?\s*([^\}]+)\s*\}?', ann_str)
        if m:
            inner = m.group(1)
            m2 = re.search(r'RequestMethod\.([A-Z_]+)', inner)
            if m2:
                return m2.group(1)
        return None

    def _join_paths(self, base: str, path: str):
        if not base:
            base = ''
        if not path:
            path = ''
        parts = [p.strip('/') for p in (base, path) if p and p.strip('/')]
        if not parts:
            return ''
        return '/' + '/'.join(parts)


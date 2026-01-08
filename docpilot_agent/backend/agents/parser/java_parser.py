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

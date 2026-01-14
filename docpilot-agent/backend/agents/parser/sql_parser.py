import re
from .base_parser import BaseParser

class SQLParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # Counts
        selects = len(re.findall(r"\bSELECT\b", code, re.I))
        inserts = len(re.findall(r"\bINSERT\b", code, re.I))
        updates = len(re.findall(r"\bUPDATE\b", code, re.I))
        deletes = len(re.findall(r"\bDELETE\b", code, re.I))

        # CREATE TABLE parsing (basic)
        tables = []
        for m in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`?([\w_]+)`?\.)?`?([\w_]+)`?\s*\((.*?)\)\s*(?:;|$)", code, re.I | re.S):
            schema = m.group(1)
            name = m.group(2)
            body = m.group(3)
            columns = []
            pks = []
            fks = []
            # split by commas that end lines or are at top-level parentheses
            parts = re.split(r",\s*(?![^()]*\))", body)
            for part in parts:
                part = part.strip().rstrip(',')
                # column definition
                colm = re.match(r"^`?([\w_]+)`?\s+([A-Za-z0-9_\(\)]+)\s*(.*)$", part, re.I)
                if colm:
                    colname = colm.group(1)
                    coltype = colm.group(2)
                    rest = colm.group(3)
                    if re.search(r"PRIMARY\s+KEY", rest, re.I):
                        pks.append(colname)
                    # detect inline foreign key
                    fk_inline = re.search(r"REFERENCES\s+`?([\w_]+)`?\s*\(`?([\w_]+)`?\)", rest, re.I)
                    if fk_inline:
                        fks.append({"column": colname, "ref_table": fk_inline.group(1), "ref_column": fk_inline.group(2)})
                    columns.append({"name": colname, "type": coltype, "constraints": rest.strip()})
                else:
                    # table constraints like PRIMARY KEY (a,b), FOREIGN KEY (...) REFERENCES t(c)
                    pkm = re.match(r"PRIMARY\s+KEY\s*\(([^)]+)\)", part, re.I)
                    if pkm:
                        cols = [c.strip().strip('`') for c in pkm.group(1).split(',')]
                        pks.extend(cols)
                    fkm = re.match(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+`?([\w_]+)`?\s*\(([^)]+)\)", part, re.I)
                    if fkm:
                        cols = [c.strip().strip('`') for c in fkm.group(1).split(',')]
                        ref_table = fkm.group(2)
                        ref_cols = [c.strip().strip('`') for c in fkm.group(3).split(',')]
                        for c, rc in zip(cols, ref_cols):
                            fks.append({"column": c, "ref_table": ref_table, "ref_column": rc})

            tables.append({"schema": schema, "name": name, "columns": columns, "primary_keys": list(dict.fromkeys(pks)), "foreign_keys": fks})

        # CREATE VIEW
        views = []
        for m in re.finditer(r"CREATE\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([\w_\.]+)`?\s+AS\s+(SELECT[\s\S]*?)(?:;|$)", code, re.I):
            views.append({"name": m.group(1), "definition": m.group(2).strip()})

        # CREATE FUNCTION/PROCEDURE
        functions = []
        for m in re.finditer(r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\s+`?([\w_\.]+)`?\s*\(([^)]*)\)\s*(RETURNS\s+[^\s]+)?\s*(AS|LANGUAGE|BEGIN)", code, re.I):
            name = m.group(1)
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            returns = m.group(3)
            functions.append({"name": name, "params": params, "returns": returns})

        # simple heuristic to capture SELECT statements (with limit to 3 examples)
        selects_examples = []
        for m in re.finditer(r"(SELECT[\s\S]{1,300}?(?:FROM\s+[\w_\.]+))", code, re.I):
            selects_examples.append(m.group(1).strip())
            if len(selects_examples) >= 3:
                break

        return {
            "file": file_path,
            "language": "sql",
            "counts": {"selects": selects, "inserts": inserts, "updates": updates, "deletes": deletes},
            "tables": tables,
            "views": views,
            "functions": functions,
            "select_examples": selects_examples,
            "comments": {"single_line": single_line, "block": block}
        }

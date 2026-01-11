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

        # module docstring
        module_doc = ast.get_docstring(tree)

        # imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.append({"name": n.name, "asname": n.asname})
            elif isinstance(node, ast.ImportFrom):
                imports.append({"module": node.module, "names": [{"name": n.name, "asname": n.asname} for n in node.names], "level": node.level})

        # helpers
        def _expr_to_str(node):
            if node is None:
                return None
            try:
                return ast.unparse(node)
            except Exception:
                return None

        def _parse_parameters(fn_node):
            params = []
            args = fn_node.args
            # positional args
            total_args = args.args
            defaults = [None] * (len(total_args) - len(args.defaults)) + list(args.defaults)
            for a, d in zip(total_args, defaults):
                params.append({
                    "name": a.arg,
                    "annotation": _expr_to_str(a.annotation),
                    "default": _expr_to_str(d) if d is not None else None,
                    "kind": "arg"
                })
            # vararg
            if args.vararg:
                params.append({"name": args.vararg.arg, "annotation": _expr_to_str(args.vararg.annotation), "kind": "vararg"})
            # kwonly args
            for a, d in zip(args.kwonlyargs, args.kw_defaults):
                params.append({"name": a.arg, "annotation": _expr_to_str(a.annotation), "default": _expr_to_str(d) if d is not None else None, "kind": "kwonly"})
            # kwarg
            if args.kwarg:
                params.append({"name": args.kwarg.arg, "annotation": _expr_to_str(args.kwarg.annotation), "kind": "kwarg"})
            return params

        def _parse_decorators(decorator_list):
            decs = []
            for d in decorator_list:
                name = None
                args = []
                kwargs = {}
                if isinstance(d, ast.Call):
                    name = _expr_to_str(d.func)
                    args = [_expr_to_str(a) for a in d.args]
                    for k in d.keywords:
                        kwargs[k.arg] = _expr_to_str(k.value)
                else:
                    name = _expr_to_str(d)
                decs.append({"name": name, "args": args, "kwargs": kwargs})
            return decs

        def _is_endpoint_decorator(dec):
            if not dec or 'name' not in dec:
                return False
            nm = (dec['name'] or '').lower()
            # fastapi/router style: router.get, app.get, get (imported)
            if any(part in nm for part in ['.get', '.post', '.put', '.delete', '.patch', '.head', '.options', '.route']) or nm.endswith('route') or nm in ('get', 'post', 'put', 'delete', 'patch'):
                return True
            return False

        endpoints = []

        # parse classes and functions as top-level items
        classes = []
        functions = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_obj = {
                    "name": node.name,
                    "bases": [_expr_to_str(b) for b in node.bases],
                    "decorators": _parse_decorators(node.decorator_list),
                    "docstring": ast.get_docstring(node),
                    "methods": [],
                    "attributes": []
                }
                for cbody in node.body:
                    if isinstance(cbody, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m = {
                            "name": cbody.name,
                            "async": isinstance(cbody, ast.AsyncFunctionDef),
                            "params": _parse_parameters(cbody),
                            "returns": _expr_to_str(cbody.returns),
                            "decorators": _parse_decorators(cbody.decorator_list),
                            "docstring": ast.get_docstring(cbody)
                        }
                        class_obj['methods'].append(m)
                        # endpoint detection on methods
                        for dec in m['decorators']:
                            if _is_endpoint_decorator(dec):
                                methods = []
                                path = None
                                if dec['args']:
                                    path = dec['args'][0]
                                if 'kwargs' in dec and dec['kwargs'].get('methods'):
                                    methods_val = dec['kwargs'].get('methods')
                                    methods = [methods_val] if isinstance(methods_val, str) else methods
                                endpoints.append({"class": node.name, "function": cbody.name, "methods": methods, "path": path, "decorator": dec})
                    elif isinstance(cbody, ast.Assign):
                        targets = [t.id for t in cbody.targets if isinstance(t, ast.Name)]
                        if targets:
                            class_obj['attributes'].extend(targets)
                classes.append(class_obj)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn = {
                    "name": node.name,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "params": _parse_parameters(node),
                    "returns": _expr_to_str(node.returns),
                    "decorators": _parse_decorators(node.decorator_list),
                    "docstring": ast.get_docstring(node)
                }
                functions.append(fn)
                # endpoint detection on functions
                for dec in fn['decorators']:
                    if _is_endpoint_decorator(dec):
                        methods = []
                        path = None
                        if dec['args']:
                            path = dec['args'][0]
                        if 'kwargs' in dec and dec['kwargs'].get('methods'):
                            methods_val = dec['kwargs'].get('methods')
                            methods = [methods_val] if isinstance(methods_val, str) else methods
                        endpoints.append({"class": None, "function": node.name, "methods": methods, "path": path, "decorator": dec})

        return {
            "file": file_path,
            "language": "python",
            "module_docstring": module_doc,
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "endpoints": endpoints
        }

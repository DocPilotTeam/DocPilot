import re
from .base_parser import BaseParser

class JSParser(BaseParser):

    def parse_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        imports = self._parse_imports(code)
        exports = self._parse_exports(code)
        functions = self._parse_functions(code)
        classes = self._parse_classes(code)
        react_components = self._parse_react_components(code)
        routes = self._parse_routes(code)
        api_calls = self._parse_api_calls(code)
        jsdoc = self._parse_jsdoc(code)
        comments = self._parse_comments(code)

        return {
            "file": file_path,
            "language": "javascript",
            "imports": imports,
            "exports": exports,
            "classes": classes,
            "functions": functions,
            "react_components": react_components,
            "routes": routes,
            "api_calls": api_calls,
            "jsdoc": jsdoc,
            "comments": comments,
        }

    # -------------------------
    # Helpers: imports, exports, functions, components, routes, api calls
    # -------------------------
    def _parse_imports(self, code):
        imports = []
        # side-effect imports: import 'module';
        for m in re.finditer(r"import\s+['\"]([^'\"]+)['\"]", code):
            imports.append({"module": m.group(1), "default": None, "named": [], "namespace": None, "side_effect": True})

        # import ... from 'module'
        for m in re.finditer(r"import\s+(?P<what>[^;]+?)\s+from\s+['\"](?P<from>[^'\"]+)['\"]", code):
            what = m.group('what').strip()
            module = m.group('from')
            default = None
            named = []
            namespace = None
            if what.startswith('{'):
                named = [i.strip() for i in what.strip('{} ').split(',') if i.strip()]
            elif what.startswith('* as'):
                namespace = what.split('as', 1)[1].strip()
            elif ',' in what:
                parts = [p.strip() for p in what.split(',', 1)]
                default = parts[0]
                rest = parts[1]
                if rest.startswith('{'):
                    named = [i.strip() for i in rest.strip('{} ').split(',') if i.strip()]
            else:
                default = what
            imports.append({"module": module, "default": default, "named": named, "namespace": namespace, "side_effect": False})

        # CommonJS require: const x = require('module')
        for m in re.finditer(r"(?:const|let|var)\s+(?P<name>\w+)\s*=\s*require\(['\"](?P<module>[^'\"]+)['\"]\)", code):
            imports.append({"module": m.group('module'), "default": m.group('name'), "named": [], "namespace": None, "side_effect": False, "require": True})

        return imports

    def _parse_exports(self, code):
        exports = {"named": [], "default": None, "module_exports": []}
        # export default <name|expr>
        m = re.search(r'export\s+default\s+([A-Za-z0-9_$.]+)', code)
        if m:
            exports['default'] = m.group(1)

        # export function/class/const name
        for m in re.finditer(r'export\s+(?:const|let|var|function|class)\s+([A-Za-z0-9_]+)', code):
            exports['named'].append(m.group(1))

        # export { a, b as c }
        for m in re.finditer(r'export\s*\{([^}]+)\}', code):
            names = [n.strip().split(' as ')[-1] for n in m.group(1).split(',') if n.strip()]
            exports['named'].extend(names)

        # module.exports = ...
        for m in re.finditer(r'module\.exports\s*=\s*([^;\n]+)', code):
            exports['module_exports'].append(m.group(1).strip())

        return exports

    def _find_preceding_jsdoc(self, code, start_pos):
        # find last /** ... */ before start_pos and ensure it's adjacent (only whitespace/newlines between)
        snippet = code[max(0, start_pos-1000):start_pos]
        m = re.search(r'/\*\*[\s\S]*?\*/\s*$', snippet)
        return m.group(0).strip() if m else None

    def _parse_functions(self, code):
        funcs = []
        # declarations: [export] [async] function name(params)
        for m in re.finditer(r'(?P<export>export\s+)?(?P<async>async\s+)?function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)', code):
            start = m.start()
            jsdoc = self._find_preceding_jsdoc(code, start)
            funcs.append({
                "name": m.group('name'),
                "params": [p.strip() for p in m.group('params').split(',') if p.strip()],
                "async": bool(m.group('async')),
                "exported": bool(m.group('export')),
                "jsdoc": jsdoc
            })

        # arrow / function expressions assigned to vars: [export] const name = [async] (...) => ...
        for m in re.finditer(r'(?P<export>export\s+)?(?P<var>const|let|var)\s+(?P<name>\w+)\s*=\s*(?P<async>async\s+)?\(?([^=]*)\)?\s*=>', code):
            start = m.start()
            jsdoc = self._find_preceding_jsdoc(code, start)
            params_raw = re.search(r"\(\s*([^)]*)\)\s*=>", code[m.start():m.end()+200])
            params = []
            if params_raw:
                params = [p.strip() for p in params_raw.group(1).split(',') if p.strip()]
            funcs.append({
                "name": m.group('name'),
                "params": params,
                "async": bool(m.group('async')),
                "exported": bool(m.group('export')),
                "arrow": True,
                "jsdoc": jsdoc
            })

        return funcs

    def _parse_classes(self, code):
        classes = []
        for m in re.finditer(r'class\s+(?P<name>\w+)(?:\s+extends\s+(?P<extends>[\w.]+))?', code):
            classes.append({
                "name": m.group('name'),
                "extends": m.group('extends') or None
            })
        return classes

    def _parse_react_components(self, code):
        components = []
        # class components
        for m in re.finditer(r'class\s+(?P<name>\w+)\s+extends\s+(?P<base>[\w.]+)', code):
            base = m.group('base')
            if base.endswith('Component'):
                components.append({"name": m.group('name'), "type": 'class', "base": base})

        # function components: capitalized name and JSX return nearby
        for m in re.finditer(r'function\s+(?P<name>[A-Z]\w+)\s*\((?P<params>[^)]*)\)', code):
            post = code[m.end():m.end()+400]
            if re.search(r'return\s*<', post):
                components.append({"name": m.group('name'), "type": 'function', "params": [p.strip() for p in m.group('params').split(',') if p.strip()]})

        for m in re.finditer(r'(?P<var>const|let|var)\s+(?P<name>[A-Z]\w+)\s*=\s*\(?([^=]*)\)?\s*=>', code):
            post = code[m.end():m.end()+400]
            if re.search(r'=>\s*<|return\s*<', post):
                components.append({"name": m.group('name'), "type": 'arrow', "params": []})

        return components

    def _parse_routes(self, code):
        routes = []
        # app.get('/path', middleware?, handler)
        for m in re.finditer(r'(?P<app>\w+)\.(?P<method>get|post|put|delete|patch|use)\s*\(\s*(["\'])(?P<path>[^"\']*)\3\s*,\s*(?P<handlers>[^)]*)\)', code):
            handlers_raw = m.group('handlers')
            handlers = [h.strip() for h in re.split(r',\s*(?=[\w\(])', handlers_raw) if h.strip()]
            routes.append({
                "app": m.group('app'),
                "method": m.group('method').upper(),
                "path": m.group('path'),
                "handlers": handlers
            })

        # router = express.Router(); router.get('/x', handler)
        for m in re.finditer(r'(?P<router>\w+)\.(?P<method>get|post|put|delete|patch|use)\s*\(\s*(["\'])(?P<path>[^"\']*)\3\s*,\s*(?P<handlers>[^)]*)\)', code):
            handlers_raw = m.group('handlers')
            handlers = [h.strip() for h in re.split(r',\s*(?=[\w\(])', handlers_raw) if h.strip()]
            routes.append({
                "router": m.group('router'),
                "method": m.group('method').upper(),
                "path": m.group('path'),
                "handlers": handlers
            })

        return routes

    def _parse_api_calls(self, code):
        calls = []
        # axios.method(url, ...)
        for m in re.finditer(r'axios\.(?P<method>get|post|put|delete|patch|request)\s*\(\s*(?P<url>[^,\)]+)(?:,\s*(?P<opts>[^\)]+))?\)', code):
            url = m.group('url').strip()
            opts = m.group('opts')
            method = m.group('method').upper() if m.group('method') else 'REQUEST'
            calls.append({"type": 'axios', "method": method, "url": url, "options": opts.strip() if opts else None})

        # fetch(url, { method: 'POST', ... })
        for m in re.finditer(r'fetch\s*\(\s*(?P<url>[^,\)]+)(?:,\s*(?P<opts>\{[^\)]*\}))?\)', code):
            url = m.group('url').strip()
            opts = m.group('opts')
            method = None
            if opts:
                mm = re.search(r"method\s*:\s*['\"](GET|POST|PUT|DELETE|PATCH)['\"]", opts, re.IGNORECASE)
                if mm:
                    method = mm.group(1).upper()
            calls.append({"type": 'fetch', "method": method or 'GET', "url": url, "options": opts})

        return calls

    def _parse_jsdoc(self, code):
        return re.findall(r'/\*\*[\s\S]*?\*/', code)

    def _parse_comments(self, code):
        single = re.findall(r'//.*', code)
        multi = re.findall(r'/\*[\s\S]*?\*/', code)
        return {"single_line": single, "multi_line": multi}

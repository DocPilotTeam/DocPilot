from .language_detector import detect_language
from .python_parser import PythonParser
from .java_parser import JavaParser
from .js_parser import JSParser
from .typescript_parser import TypeScriptParser
from .golang_parser import GoParser
from .llm_fallback_parser import LLMFallbackParser
from .ruby_parser import RubyParser
from .kotlin_parser import KotlinParser
from .rust_parser import RustParser
from .cpp_parser import CppParser
from .c_parser import CParser
from .csharp_parser import CSharpParser
from .php_parser import PHPParser
from .swift_parser import SwiftParser
from .objectivec_parser import ObjectiveCParser
from .sql_parser import SQLParser

class ParserManager:

    def __init__(self, llm_client=None):
        self.parsers = {
            "python": PythonParser(),
            "java": JavaParser(),
            "javascript": JSParser(),
            "typescript": TypeScriptParser(),
            "go": GoParser(),
            "ruby": RubyParser(),
            "kotlin": KotlinParser(),
            "rust": RustParser(),
            "cpp": CppParser(),
            "c": CParser(),
            "csharp": CSharpParser(),
            "php": PHPParser(),
            "swift": SwiftParser(),
            "objectivec": ObjectiveCParser(),
            "sql": SQLParser(),
        }

        self.llm_fallback = LLMFallbackParser()

    def parse(self, file_path: str) -> dict | None:
        lang = detect_language(file_path)
        if not lang:
            # Unknown extension — use LLM fallback with extension as a hint
            from pathlib import Path
            ext = Path(file_path).suffix.lstrip('.').lower() or 'unknown'
            return self.llm_fallback.parse_file(file_path, ext)

        # Use static parser if available
        if lang in self.parsers:
            return self.parsers[lang].parse_file(file_path)


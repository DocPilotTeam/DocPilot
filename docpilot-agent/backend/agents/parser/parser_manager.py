from .language_detector import detect_language
from .python_parser import PythonParser
from .java_parser import JavaParser
from .js_parser import JSParser
from .typescript_parser import TypeScriptParser
from .llm_fallback_parser import LLMFallbackParser

class ParserManager:

    def __init__(self, llm_client=None):
        self.parsers = {
            "python": PythonParser(),
            "java": JavaParser(),
            "javascript": JSParser(),
            "typescript": TypeScriptParser()
        }

        self.llm_fallback = LLMFallbackParser()

    def parse(self, file_path: str) -> dict | None:
        lang = detect_language(file_path)
        if not lang:
            return None

        # Use static parser if available
        if lang in self.parsers:
            return self.parsers[lang].parse_file(file_path)

        # Use LLM only for supported-but-not-implemented languages
        return self.llm_fallback.parse_file(file_path, lang)


from pathlib import Path

EXT_TO_LANG = {
    "py": "python",
    "java": "java",
    "js": "javascript",
    "ts": "typescript",
    "go": "go",
    "rb": "ruby",
    "kt": "kotlin",
    "rs": "rust",
    "cpp": "cpp",
    "c": "c",
    "cs": "csharp",
    "php": "php",
    "swift": "swift",
    "cs": "csharp",
    "m": "objectivec"
}

def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lstrip(".").lower()
    return EXT_TO_LANG.get(ext, None)

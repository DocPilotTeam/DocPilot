class BaseParser:
    """
    A base class for all parser implementations.
    Every parser returns a dict with:
    {
        "file": <file_path>,
        "language": <language>,
        ...
    }
    """
    def parse_file(self, file_path: str) -> dict:
        raise NotImplementedError("parse_file() must be implemented by subclasses")

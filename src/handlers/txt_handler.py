from .base_handler import BaseHandler

class TxtHandler(BaseHandler):
    def extract_text(self, file_path: str, **kwargs) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (FileNotFoundError, UnicodeDecodeError) as e:
            raise RuntimeError(f"Failed to read TXT file '{file_path}': {e}")

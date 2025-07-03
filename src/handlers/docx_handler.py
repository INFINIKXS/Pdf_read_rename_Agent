from .base_handler import BaseHandler


class DocxHandler(BaseHandler):
    def extract_text(self, file_path: str, **kwargs) -> str:
        """
        Extract text from a DOCX file using python-docx.
        Args:
            file_path (str): Path to the DOCX file.
        Returns:
            str: Extracted text content.
        Raises:
            RuntimeError: If the file cannot be read or parsed as DOCX.
        """
        try:
            import docx
        except ImportError as e:
            raise RuntimeError("python-docx is required to extract DOCX text. Please install it via 'pip install python-docx'.") from e
        try:
            doc = docx.Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs if p.text])
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from DOCX file '{file_path}': {e}")

from .base_handler import BaseHandler

class PdfHandler(BaseHandler):
    def extract_text(self, file_path: str, **kwargs) -> str:
        """
        Extracts text from a PDF file using pypdf.
        Args:
            file_path (str): Path to the PDF file.
            **kwargs: Additional options (not used).
        Returns:
            str: Extracted text content from all pages.
        Raises:
            RuntimeError: If the file cannot be read or parsed as PDF.
        """
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise RuntimeError("pypdf is required to extract PDF text. Please install it via 'pip install pypdf'.") from e

        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF file '{file_path}': {e}")

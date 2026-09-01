from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class ResumeValidationError(ValueError):
    pass


class PdfResumeParser:
    def __init__(self, max_bytes: int) -> None:
        self._max_bytes = max_bytes

    def parse(self, *, content: bytes, content_type: str | None, filename: str | None) -> str:
        if content_type != "application/pdf":
            raise ResumeValidationError("Resume must use the application/pdf content type.")
        if not filename or not filename.casefold().endswith(".pdf"):
            raise ResumeValidationError("Resume filename must end in .pdf.")
        if not content or len(content) > self._max_bytes:
            raise ResumeValidationError("Resume PDF must be between 1 byte and 5 MB.")
        if not content.startswith(b"%PDF"):
            raise ResumeValidationError("Uploaded file is not a valid PDF.")
        try:
            reader = PdfReader(BytesIO(content))
            raw_text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except (PdfReadError, ValueError) as error:
            raise ResumeValidationError("Resume PDF could not be parsed.") from error
        if not raw_text:
            raise ResumeValidationError("Resume PDF does not contain extractable text.")
        return raw_text

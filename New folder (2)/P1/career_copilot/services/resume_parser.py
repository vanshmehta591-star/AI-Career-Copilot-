"""Resume parser — extracts plain text from PDF or TXT files."""

import io


class ResumeParser:
    """Parse uploaded resume files (PDF or TXT) into plain text."""

    MAX_FILE_SIZE_MB: int = 5

    def parse(self, file_bytes: bytes, filename: str) -> str:
        """Extract text from *file_bytes*.

        Parameters
        ----------
        file_bytes:
            Raw bytes of the uploaded file.
        filename:
            Original file name; used to determine file type.

        Returns
        -------
        str
            Extracted plain text.

        Raises
        ------
        ValueError
            If the file type is unsupported or the file exceeds MAX_FILE_SIZE_MB.
        """
        max_bytes = self.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ValueError(
                f"File size exceeds {self.MAX_FILE_SIZE_MB} MB limit."
            )

        lower_name = filename.lower()
        if lower_name.endswith(".txt"):
            return file_bytes.decode("utf-8", errors="replace")

        if lower_name.endswith(".pdf"):
            return self._parse_pdf(file_bytes)

        raise ValueError(
            f"Unsupported file type '{filename}'. Only PDF and TXT are accepted."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_pdf(self, file_bytes: bytes) -> str:
        """Extract text from a PDF using PyPDF2."""
        try:
            import PyPDF2  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "PyPDF2 is required for PDF parsing. Install it with: pip install pypdf2"
            ) from exc

        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n".join(parts)

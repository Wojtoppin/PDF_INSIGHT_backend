class PDFInsightError(Exception):
    """Base class for errors that carry a user-facing, Polish message.

    Caught by a single exception handler in app.main so every endpoint
    returns the same {"error": "..."} shape without repeating try/except.
    """

    status_code: int = 500
    message: str = "Wystąpił nieoczekiwany błąd."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message


class InvalidFileError(PDFInsightError):
    status_code = 400
    message = "Plik musi być w formacie PDF i nie przekraczać dozwolonego rozmiaru."


class NoTextLayerError(PDFInsightError):
    status_code = 422
    message = (
        "Nie wykryto warstwy tekstowej w dokumencie (prawdopodobnie skan). "
        "Ta wersja nie obsługuje jeszcze OCR."
    )


class SuspiciousContentError(PDFInsightError):
    status_code = 422
    message = "Dokument został odrzucony ze względów bezpieczeństwa."


class AnalysisFailedError(PDFInsightError):
    status_code = 502
    message = "Nie udało się przeanalizować dokumentu. Spróbuj ponownie."

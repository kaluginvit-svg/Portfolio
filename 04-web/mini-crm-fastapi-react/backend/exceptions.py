class AppException(Exception):
    def __init__(self, code: str, message: str, detail: str | None = None, status: int = 400):
        self.code = code
        self.message = message
        self.detail = detail
        self.status = status
        super().__init__(message)

class ModerationAPIError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(message)


class ReportNotFound(ModerationAPIError):
    pass

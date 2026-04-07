from __future__ import annotations


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }


class ValidationAPIError(APIError):
    def __init__(self, code: str, message: str):
        super().__init__(code=code, message=message, status_code=400)


class ProviderAPIError(APIError):
    def __init__(self, code: str, message: str, status_code: int = 502):
        super().__init__(code=code, message=message, status_code=status_code)


class InternalAPIError(APIError):
    def __init__(self):
        super().__init__(
            code="internal_error",
            message="Ocorreu um erro interno. Tente novamente em instantes.",
            status_code=500,
        )

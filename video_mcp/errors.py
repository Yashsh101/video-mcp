from enum import Enum


class ErrorCode(str, Enum):
    PATH_VIOLATION = "PATH_VIOLATION"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    TIMEOUT = "TIMEOUT"
    INVALID_INPUT = "INVALID_INPUT"
    ASSEMBLY_FAILED = "ASSEMBLY_FAILED"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"

class MCPVideoError(Exception):
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        hint: str | None = None,
        recoverable: bool = False,
        provider: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.hint = hint
        self.recoverable = recoverable
        self.provider = provider

    def __str__(self) -> str:
        prov_str = f" [{self.provider}]" if self.provider else ""
        hint_str = f" Hint: {self.hint}" if self.hint else ""
        return f"{self.code.value}{prov_str}: {self.message}{hint_str}"

def raise_provider_error(provider: str, status_code: int, body: str) -> None:
    """Maps HTTP status codes from providers to typed MCPVideoErrors."""
    message = f"Provider request failed with status {status_code}: {body}"
    code = ErrorCode.PROVIDER_ERROR
    hint = "Verify your API key and connection."
    recoverable = False

    if status_code == 429:
        message = f"Rate limit exceeded or insufficient quota on {provider}"
        code = ErrorCode.QUOTA_EXCEEDED
        hint = "Wait before retrying or top up your account balance."
        recoverable = True
    elif status_code == 401 or status_code == 403:
        message = f"Authentication failed for provider {provider}"
        code = ErrorCode.PROVIDER_ERROR
        hint = f"Check that your {provider.upper()}_API_KEY is configured correctly."
    elif status_code >= 500:
        message = f"Provider {provider} returned server error ({status_code})"
        code = ErrorCode.PROVIDER_ERROR
        hint = "This is a temporary provider issue. Retrying may succeed."
        recoverable = True

    raise MCPVideoError(
        message=message,
        code=code,
        hint=hint,
        recoverable=recoverable,
        provider=provider,
    )

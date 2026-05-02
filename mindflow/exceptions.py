class OrganizeError(Exception):
    """Base for organize workflow errors."""

    code = "organize_error"


class RateLimitExceeded(OrganizeError):
    code = "rate_limit_exceeded"

    def __init__(self, message: str, retry_after_seconds: int | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class BatchTooLarge(OrganizeError):
    code = "batch_too_large"


class InvalidState(OrganizeError):
    code = "invalid_state"


class InferenceError(OrganizeError):
    code = "inference_error"


class NoInboxItems(OrganizeError):
    code = "no_inbox_items"

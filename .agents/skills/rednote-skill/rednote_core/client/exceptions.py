"""Custom exceptions for the RedNote HTTP client."""


class RedNoteError(Exception):
    """Base exception for all RedNote errors."""
    pass


class CryptoError(RedNoteError):
    """Raised when request signing fails."""
    pass


class AuthError(RedNoteError):
    """Raised when authentication is invalid or expired.

    The user should re-run `rednote login` to refresh credentials.
    """
    pass


class RateLimitError(RedNoteError):
    """Raised when the API returns 429 Too Many Requests."""
    pass


class SecurityChallenge(RedNoteError):
    """Raised when the API returns 461 security challenge.

    The client middleware automatically attempts to refresh
    signing parameters and retry once before surfacing this.
    """
    pass


class ParseError(RedNoteError):
    """Raised when API response parsing fails."""
    pass

"""Errors file."""


class BaseError(Exception):
    """Base exception of project."""

    def __init__(self, msg, code):
        """Message and error code."""
        self.msg = msg
        self.code = code


class TokenCheckError(BaseError):
    """Token doesn't exist."""


class HttpResponseError(BaseError):
    """API response error."""


class RequestError(BaseError):
    """Request failed."""


class StatusIsNotOK(BaseError):
    """When status code not 200."""

"""Errors file."""


class ProjectException(Exception):
    """Base exception of project."""


class TokenIsNoneError(ProjectException):
    """Error raised when token is not defined."""


class HttpResponseError(ProjectException):
    """API response error."""


class RequestError(ProjectException):
    """Request failed."""

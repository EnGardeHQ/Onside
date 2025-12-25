"""Authentication services package."""

# Import all authentication services here
from .google_oauth import GoogleOAuth  # noqa: F401

__all__ = ["GoogleOAuth"]

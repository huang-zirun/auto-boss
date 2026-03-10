"""核心模块"""
from .exceptions import (
    BossHelperError,
    BrowserError,
    LoginError,
    LoginTimeoutError,
    ElementNotFoundError,
    ElementNotInteractableError,
    RiskControlDetectedError,
    ConfigurationError,
)

__all__ = [
    "BossHelperError",
    "BrowserError",
    "LoginError",
    "LoginTimeoutError",
    "ElementNotFoundError",
    "ElementNotInteractableError",
    "RiskControlDetectedError",
    "ConfigurationError",
]

# -*- coding: utf-8 -*-
"""Project settings."""
import logging
import os
from enum import Enum
from enum import IntEnum
from pathlib import Path
from typing import Optional
from typing import Union

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic import BaseSettings

from media_scraper.exc import EnvVarNotFound


def init_dotenv():
    """Loc n' load dotenv file.

    Sets the location for a dotenv file containig envvars loads its
    contents.
    Raises:
        FileNotFoundError: When the selected location does not
        correspond to a file.
    Returns:
        Location of the dotenv file.

    """

    candidate = find_dotenv(usecwd=True)

    if not candidate:
        # raise IOError(f"Can't find .env file")
        return

    load_dotenv(candidate)


class LogLevel(IntEnum):
    """Explicitly define allowed logging levels."""

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    TRACE = 1 + logging.NOTSET
    NOTSET = logging.NOTSET


class LogDest(Enum):
    """Define allowed destinations for logs."""

    CONSOLE = "CONSOLE"
    """Log to console"""

    FILE = "FILE"
    """Log to file"""


class LogFormatter(Enum):
    """Define allowed destinations for logs."""

    JSON = "JSON"
    """JSONs, eg for filebeat or similar, for machines"""

    COLOR = "COLOR"
    """pprinted, colored, for humans"""


class Settings(BaseSettings):
    """Configuraciones comumnes."""


class Production(Settings):
    """Configuraciones ambiente de producción."""

    ELASTICSEARCH_HOST: str
    LOG_FORMAT: str = LogFormatter.JSON.value
    LOG_LEVEL: int = LogLevel.WARNING.value
    LOG_DESTINATION: str = LogDest.FILE.value


class Development(Settings):
    """Configuraciones ambiente de desarrollo."""

    LOG_FORMAT: str = LogFormatter.COLOR.value  # requires colorama
    LOG_LEVEL: int = LogLevel.INFO.value
    LOG_DESTINATION: str = LogDest.CONSOLE.value


def init_project_settings():
    """Returns settings via project mode env var."""

    init_dotenv()

    mode = os.environ.get("PROJECT_MODE")

    if not mode:
        raise EnvVarNotFound(env_var="PROJECT_MODE")

    if mode == "Development":
        return Development()

    elif mode == "Production":
        return Production()

    else:
        raise ValueError(
            "env_var `PROJECT_MODE` debe ser `Development` o `Production`"
        )

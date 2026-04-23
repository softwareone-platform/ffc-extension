import logging.config

import rich
from rich.highlighter import ReprHighlighter
from rich.logging import RichHandler as _RichHandler
from rich.theme import Theme

from app.conf import Settings
from app.db import models


class FFCOpsHighlighter(ReprHighlighter):
    prefixes = (
        models.Account.PK_PREFIX,
        models.Actor.PK_PREFIX,
        models.Entitlement.PK_PREFIX,
        models.Organization.PK_PREFIX,
        models.System.PK_PREFIX,
        models.User.PK_PREFIX,
    )
    highlights = list(ReprHighlighter.highlights) + [
        rf"(?P<ffcops_id>(?:{'|'.join(prefixes)})(?:-\d{{4}})*)"
    ]


class RichHandler(_RichHandler):
    """Rich handler for logging with color support."""

    HIGHLIGHTER_CLASS = FFCOpsHighlighter


rich.reconfigure(theme=Theme({"repr.ffcops_id": "bold light_salmon3"}))


def get_logging_config(settings: Settings) -> dict:
    log_level = "DEBUG" if settings.debug else "INFO"
    handler = "rich" if settings.cli_rich_logging else "console"
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{asctime} {name} {levelname} (pid: {process}) {message}",
                "style": "{",
            },
            "rich": {
                "format": "{name} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
                "stream": "ext://sys.stderr",
            },
            "rich": {
                "class": "app.logging.RichHandler",
                "level": log_level,
                "formatter": "rich",
                "log_time_format": "%Y-%m-%d %H:%M:%S",
                "rich_tracebacks": True,
                "highlighter": "",
            },
        },
        "root": {
            "handlers": [handler],
            "level": "WARNING",
        },
        "loggers": {
            "gunicorn.access": {
                "handlers": [handler],
                "level": log_level,
                "propagate": False,
            },
            "gunicorn.error": {
                "handlers": [handler],
                "level": log_level,
                "propagate": False,
            },
            "app": {
                "handlers": [handler],
                "level": log_level,
                "propagate": False,
            },
            "mrok": {
                "handlers": [handler],
                "level": log_level,
                "propagate": False,
            },
        },
    }

    return logging_config


def setup_logging(settings: Settings) -> None:
    logging_config = get_logging_config(settings)
    logging.config.dictConfig(logging_config)

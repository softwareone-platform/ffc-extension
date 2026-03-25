# ruff: noqa T100
import inspect

from IPython.terminal.embed import InteractiveShellEmbed
from rich import box
from rich.console import Console
from rich.table import Table

from app.conf import get_settings
from app.db.base import session_factory
from app.db import handlers
from app.db import models


def get_row(key, value):
    if key == "models":
        item_type = "ModelsPackage"
    else:
        item_type = type(value).__name__

    if key == "session":
        preview = "Asynchronous session to manage persistence operations for ORM-mapped objects"
    else:
        preview = inspect.getdoc(value) or repr(value)

    return key, item_type, preview[:60]


def command():
    """
    Run the shell command.
    """
    session = session_factory()
    namespace = {
        "settings": get_settings(),
        "session": session,
        "models": models,
        "user_handler": handlers.UserHandler(session),
        "account_handler": handlers.AccountHandler(session),
        "account_user_handler": handlers.AccountUserHandler(session),
        "entitlement_handler": handlers.EntitlementHandler(session),
        "system_handler": handlers.SystemHandler(session),
        "organization_handler": handlers.OrganizationHandler(session),
        "datasource_expense_handler": handlers.DatasourceExpenseHandler(session),
    }

    table = Table(
        box=box.ROUNDED,
        title="🔍 Available Objects in Shell Context:",
        title_justify="left",
        border_style="#472AFF",
    )
    table.add_column("Name", style="bold cyan")
    table.add_column("Type", style="green")
    table.add_column("Preview", style="dim")

    for key, val in namespace.items():
        table.add_row(*get_row(key, val))

    console = Console()
    with console.capture() as capture:
        console.print(table)

    banner = "\nFinOps for Cloud Operations API Shell\n\n"
    banner += "\n" + capture.get()
    banner += "\nType 'exit' or 'quit' to exit the shell.\n"
    banner += "Type 'help' for a list of available commands.\n"
    exit_msg = "\nBye 👋"

    ipshell = InteractiveShellEmbed(banner1=banner, exit_msg=exit_msg)
    ipshell(global_ns=namespace, local_ns=namespace)

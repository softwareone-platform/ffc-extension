from typing import Annotated

from fastapi import Depends, Request

from app.conf import Settings, get_settings
from app.schemas.core import ExtensionContext as _ExtensionContext

AppSettings = Annotated[Settings, Depends(get_settings)]


def _get_extension_context(request: Request) -> _ExtensionContext:
    if not hasattr(request.app.state, "ctx"):
        request.app.state.ctx = _ExtensionContext.from_identity_file()
    return request.app.state.ctx


ExtensionContext = Annotated[_ExtensionContext, Depends(_get_extension_context)]

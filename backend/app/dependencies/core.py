from typing import Annotated

from fastapi import Depends, Request

from app.conf import Settings, get_settings
from app.schemas.core import ExtensionContext as _ExtensionContext

AppSettings = Annotated[Settings, Depends(get_settings)]


def _get_extension_context(request: Request) -> _ExtensionContext:
    return request.app.state.ctx


ExtensionContext = Annotated[_ExtensionContext, Depends(_get_extension_context)]

from typing import Annotated

from fastapi import Depends

from app.conf import Settings, get_settings

AppSettings = Annotated[Settings, Depends(get_settings)]

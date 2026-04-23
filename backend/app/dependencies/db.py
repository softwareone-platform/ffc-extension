from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import handlers
from app.db.base import session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        async with session.begin():
            yield session


DBSession = Annotated[AsyncSession, Depends(get_db_session)]


class HandlerFactory:
    def __init__(self, handler_cls: type[handlers.ModelHandler]):
        self.handler_class = handler_cls

    def __call__(self, session: DBSession) -> handlers.ModelHandler:
        return self.handler_class(session)


EntitlementRepository = Annotated[
    handlers.EntitlementHandler, Depends(HandlerFactory(handlers.EntitlementHandler))
]
OrganizationRepository = Annotated[
    handlers.OrganizationHandler, Depends(HandlerFactory(handlers.OrganizationHandler))
]
AccountRepository = Annotated[
    handlers.AccountHandler, Depends(HandlerFactory(handlers.AccountHandler))
]
UserRepository = Annotated[handlers.UserHandler, Depends(HandlerFactory(handlers.UserHandler))]
AccountUserRepository = Annotated[
    handlers.AccountUserHandler, Depends(HandlerFactory(handlers.AccountUserHandler))
]
SystemRepository = Annotated[
    handlers.SystemHandler, Depends(HandlerFactory(handlers.SystemHandler))
]
DatasourceExpenseRepository = Annotated[
    handlers.DatasourceExpenseHandler, Depends(HandlerFactory(handlers.DatasourceExpenseHandler))
]
AdditionalAdminRequestRepository = Annotated[
    handlers.AdditionalAdminRequestHandler,
    Depends(HandlerFactory(handlers.AdditionalAdminRequestHandler)),
]

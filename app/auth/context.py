from contextvars import ContextVar
from dataclasses import dataclass

from app.db.models import Account, Actor, System, User
from app.enums import ActorType


@dataclass
class AuthenticationContext:
    account: Account
    actor_type: ActorType | None = None
    system: System | None = None
    user: User | None = None

    def get_actor(self) -> Actor | None:
        if self.actor_type == ActorType.SYSTEM:
            return self.system
        return self.user


@dataclass
class MPTAuthContext:
    account_id: str
    account_type: str
    installation_id: str
    user_id: str | None = None
    token_id: str | None = None


auth_context = ContextVar[AuthenticationContext]("auth_context")

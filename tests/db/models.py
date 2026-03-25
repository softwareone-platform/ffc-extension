import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.human_readable_pk import HumanReadablePKMixin
from app.db.models import AuditableMixin, Base


class ModelForTests(Base, HumanReadablePKMixin):
    __tablename__ = "test_models"

    PK_PREFIX = "TMDL"
    PK_NUM_LENGTH = 4

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False, default="active")
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("related_models.id"), nullable=True)
    parent: Mapped["ParentModelForTests"] = relationship(foreign_keys=[parent_id])


class ParentModelForTests(Base, HumanReadablePKMixin):
    __tablename__ = "related_models"

    PK_PREFIX = "RMDL"
    PK_NUM_LENGTH = 4
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


@enum.unique
class DeletableModelStatus(str, enum.Enum):
    ACTIVE = "active"
    DELETED = "deleted"


class DeletableModelForTests(Base, HumanReadablePKMixin):
    __tablename__ = "test_deletable_models"

    PK_PREFIX = "DMDL"
    PK_NUM_LENGTH = 4

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[DeletableModelStatus] = mapped_column(
        Enum(DeletableModelStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DeletableModelStatus.ACTIVE,
        server_default=DeletableModelStatus.ACTIVE.value,
    )


class DeletableAuditModelForTests(Base, HumanReadablePKMixin, AuditableMixin):
    __tablename__ = "test_deletable_audit_models"

    PK_PREFIX = "DAM"
    PK_NUM_LENGTH = 4

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[DeletableModelStatus] = mapped_column(
        Enum(DeletableModelStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DeletableModelStatus.ACTIVE,
        server_default=DeletableModelStatus.ACTIVE.value,
    )


@enum.unique
class NonDeletableModelStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class NonDeletableModelWithEnumStatusForTests(Base, HumanReadablePKMixin):
    __tablename__ = "test_non_deletable_with_status_models"

    PK_PREFIX = "NDMS"
    PK_NUM_LENGTH = 4

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[NonDeletableModelStatus] = mapped_column(
        Enum(NonDeletableModelStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=NonDeletableModelStatus.ACTIVE,
        server_default=NonDeletableModelStatus.ACTIVE.value,
    )

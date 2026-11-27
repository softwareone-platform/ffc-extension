"""
Project's ORM models module: defines database models such as
Account, Organization, Entitlement, etc.
"""

from __future__ import annotations

import datetime
import re
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)

from app.db.constants import (
    FKEY_ACCOUNT,
    FKEY_ACTIVITY_LOG,
    FKEY_ACTOR,
    FKEY_CLIENT_ACCOUNT,
    FKEY_ORGANIZATION,
    FKEY_USER,
)
from app.db.human_readable_pk import HumanReadablePKMixin
from app.enums import (
    AccountIntegration,
    AccountStatus,
    AccountType,
    AccountUserStatus,
    ActivityStatus,
    ActorType,
    DatasourceType,
    EntitlementStatus,
    OrganizationStatus,
    SystemStatus,
    TerminationReason,
    UserStatus,
)


class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
    )


class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC),
        server_default=sa.func.current_timestamp(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC),
        server_default=sa.func.current_timestamp(),
        onupdate=sa.func.current_timestamp(),
    )
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )


class Actor(Base, HumanReadablePKMixin):
    __tablename__ = "actors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ActorType.USER,
        server_default=ActorType.USER.value,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __mapper_args__ = {
        "polymorphic_on": "type",
    }


class App(Actor):
    __tablename__ = "apps"

    PK_PREFIX = "FAPP"
    PK_NUM_LENGTH = 4

    id: Mapped[str] = mapped_column(ForeignKey(FKEY_ACTOR), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": ActorType.APP.value,
        "inherit_condition": id == Actor.id,
        "polymorphic_load": "inline",
    }


class AuditableMixin(TimestampMixin):
    created_by_id: Mapped[str | None] = mapped_column(ForeignKey(FKEY_ACTOR), name="created_by")
    updated_by_id: Mapped[str | None] = mapped_column(ForeignKey(FKEY_ACTOR), name="updated_by")
    deleted_by_id: Mapped[str | None] = mapped_column(ForeignKey(FKEY_ACTOR), name="deleted_by")

    @declared_attr
    def created_by(cls) -> Mapped[Actor]:
        return relationship(
            "Actor",
            foreign_keys=lambda: [cls.__dict__["created_by_id"]],
            lazy="joined",
        )

    @declared_attr
    def updated_by(cls) -> Mapped[Actor]:
        return relationship(
            "Actor",
            foreign_keys=lambda: [cls.__dict__["updated_by_id"]],
            lazy="joined",
            post_update=True,
        )

    @declared_attr
    def deleted_by(cls) -> Mapped[Actor]:
        return relationship(
            "Actor",
            foreign_keys=lambda: [cls.__dict__["deleted_by_id"]],
            lazy="joined",
        )


class Account(Base, HumanReadablePKMixin, AuditableMixin):
    __tablename__ = "accounts"

    PK_PREFIX = "FACC"
    PK_NUM_LENGTH = 8

    type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=AccountType.AFFILIATE,
        server_default=AccountType.AFFILIATE.value,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    integration: Mapped[AccountIntegration] = mapped_column(
        Enum(AccountIntegration, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
        default=None,
        server_default=None,
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=AccountStatus.ACTIVE,
        server_default=AccountStatus.ACTIVE.value,
    )
    cloud_provider: Mapped[CloudProvider | None] = relationship(
        back_populates="account",
        uselist=False,
        lazy="joined",
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    users: Mapped[list[AccountUser]] = relationship(back_populates="account")
    new_entitlements_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    active_entitlements_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    terminated_entitlements_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    products: Mapped[str] = mapped_column(String(511), nullable=True)

    @property
    def account_user(self) -> AccountUser | None:
        try:
            return self.users[0]
        except Exception:
            return None


class CloudProvider(Base, HumanReadablePKMixin, AuditableMixin):
    __tablename__ = "cloud_providers"

    PK_PREFIX = "FCLP"
    PK_NUM_LENGTH = 4

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(64), nullable=False)
    datasource_id_format: Mapped[str] = mapped_column(String(512), nullable=False)
    account_id: Mapped[str] = mapped_column(ForeignKey(FKEY_ACCOUNT), nullable=False)
    account: Mapped[Account] = relationship(
        back_populates="cloud_provider", foreign_keys=[account_id]
    )

    __table_args__ = (UniqueConstraint(account_id, name="uq_cloud_providers_account_id"),)

    def matches_datasource_id(self, datasource_id: str) -> bool:
        return re.fullmatch(self.datasource_id_format, datasource_id) is not None


class System(Actor, AuditableMixin):
    __tablename__ = "systems"

    PK_PREFIX = "FTKN"
    MPT_PREFIX = "TKN"
    PK_NUM_LENGTH = 8

    id: Mapped[str] = mapped_column(ForeignKey(FKEY_ACTOR), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey(FKEY_ACCOUNT))
    owner: Mapped[Account] = relationship(foreign_keys=[owner_id])
    status: Mapped[SystemStatus] = mapped_column(
        Enum(SystemStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=SystemStatus.ACTIVE,
        server_default=SystemStatus.ACTIVE.value,
    )

    __mapper_args__ = {
        "polymorphic_identity": ActorType.SYSTEM.value,
        "inherit_condition": id == Actor.id,
        "polymorphic_load": "inline",
    }


class User(Actor, HumanReadablePKMixin, AuditableMixin):
    __tablename__ = "users"

    PK_PREFIX = "FUSR"
    MPT_PREFIX = "USR"
    PK_NUM_LENGTH = 8

    id: Mapped[str] = mapped_column(ForeignKey(FKEY_ACTOR), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=UserStatus.DRAFT,
        server_default=UserStatus.DRAFT.value,
    )
    accounts: Mapped[list[AccountUser]] = relationship(back_populates="user", lazy="raise")

    @property
    def account_user(self) -> AccountUser | None:
        try:
            return self.accounts[0]
        except Exception:
            # todo : improve this excepption
            return None

    __mapper_args__ = {
        "polymorphic_identity": ActorType.USER.value,
        "inherit_condition": id == Actor.id,
        "polymorphic_load": "inline",
    }


class AccountUser(Base, AuditableMixin, HumanReadablePKMixin):
    __tablename__ = "accounts_users"

    PK_PREFIX = "FAUR"
    PK_NUM_LENGTH = 12

    account_id: Mapped[str] = mapped_column(ForeignKey(FKEY_ACCOUNT))
    user_id: Mapped[str] = mapped_column(ForeignKey(FKEY_USER))
    account: Mapped[Account] = relationship(back_populates="users", foreign_keys=[account_id])
    user: Mapped[User] = relationship(back_populates="accounts", foreign_keys=[user_id])
    status: Mapped[AccountUserStatus] = mapped_column(
        Enum(AccountUserStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=AccountUserStatus.INVITED,
        server_default=AccountUserStatus.INVITED.value,
    )


class ClientAccount(Base, AuditableMixin, HumanReadablePKMixin):
    __tablename__ = "client_accounts"

    PK_PREFIX = "FCAC"
    PK_NUM_LENGTH = 8

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    organizations: Mapped[list[Organization]] = relationship(
        back_populates="client_account", lazy="raise"
    )

    __table_args__ = (
        Index(
            "ix_client_accounts_external_id_for_non_deleted",
            external_id,
            unique=True,
            postgresql_where=sa.text("deleted_at IS NULL"),
        ),
    )


class Organization(Base, AuditableMixin, HumanReadablePKMixin):
    __tablename__ = "organizations"

    PK_PREFIX = "FORG"
    PK_NUM_LENGTH = 12

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    billing_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    operations_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    linked_organization_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=OrganizationStatus.ACTIVE,
        server_default=OrganizationStatus.ACTIVE.value,
    )

    terminated_at: Mapped[datetime.datetime | None] = mapped_column(sa.DateTime(timezone=True))
    terminated_by_id: Mapped[str | None] = mapped_column(ForeignKey(FKEY_ACTOR))
    terminated_by: Mapped[Actor | None] = relationship(foreign_keys=[terminated_by_id])

    termination_feedback: Mapped[TerminationFeedback | None] = relationship(
        back_populates="organization",
        uselist=False,
        lazy="joined",
    )
    client_account_id: Mapped[str | None] = mapped_column(
        ForeignKey(FKEY_CLIENT_ACCOUNT), nullable=True, index=True
    )
    client_account: Mapped[ClientAccount | None] = relationship(
        back_populates="organizations", foreign_keys=[client_account_id], lazy="joined"
    )

    __table_args__ = (
        Index(
            "ix_organizations_operations_external_id_for_non_deleted",
            operations_external_id,
            unique=True,
            postgresql_where=(status != OrganizationStatus.DELETED),
        ),
    )


class TerminationFeedback(Base, TimestampMixin, HumanReadablePKMixin):
    __tablename__ = "termination_feedbacks"

    PK_PREFIX = "FFBK"
    PK_NUM_LENGTH = 12

    organization_id: Mapped[str] = mapped_column(
        ForeignKey(FKEY_ORGANIZATION), nullable=False, unique=True
    )
    organization: Mapped[Organization] = relationship(
        back_populates="termination_feedback", foreign_keys=[organization_id]
    )
    reason: Mapped[TerminationReason] = mapped_column(
        Enum(TerminationReason, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    comments: Mapped[str | None] = mapped_column(Text(), nullable=True)


class DatasourceExpense(Base, HumanReadablePKMixin, TimestampMixin):
    __tablename__ = "datasource_expenses"
    # Expense rows are imported in bulk by a job; they are data, not activity.
    __activity_log__ = False

    PK_PREFIX = "FDSX"
    PK_NUM_LENGTH = 12

    datasource_id: Mapped[str] = mapped_column(String(255), index=True)
    linked_datasource_id: Mapped[str] = mapped_column(String(255))
    linked_datasource_type: Mapped[DatasourceType] = mapped_column(
        Enum(DatasourceType, values_callable=lambda obj: [e.value for e in obj]),
    )
    datasource_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey(FKEY_ORGANIZATION))

    organization: Mapped[Organization] = relationship(lazy="raise", foreign_keys=[organization_id])

    year: Mapped[int] = mapped_column(Integer(), nullable=False)
    month: Mapped[int] = mapped_column(Integer(), nullable=False)
    day: Mapped[int] = mapped_column(Integer(), nullable=False)
    expenses: Mapped[Decimal] = mapped_column(
        sa.Numeric(18, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0.0000",
    )
    total_expenses: Mapped[Decimal] = mapped_column(sa.Numeric(18, 4), nullable=False)

    __table_args__ = (
        Index("ix_datasource_expenses_year_and_month", year, month),
        UniqueConstraint(
            datasource_id,
            linked_datasource_type,
            organization_id,
            year,
            month,
            day,
            name="uq_datasource_expenses_per_day",
        ),
    )


class Entitlement(Base, HumanReadablePKMixin, AuditableMixin):
    __tablename__ = "entitlements"

    PK_PREFIX = "FENT"
    PK_NUM_LENGTH = 12

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    affiliate_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    datasource_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    linked_datasource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_datasource_type: Mapped[DatasourceType | None] = mapped_column(
        Enum(DatasourceType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
    )
    linked_datasource_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey(FKEY_ACCOUNT), nullable=False)
    owner: Mapped[Account] = relationship(foreign_keys=[owner_id], lazy="joined")
    status: Mapped[EntitlementStatus] = mapped_column(
        Enum(EntitlementStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=EntitlementStatus.NEW,
        server_default=EntitlementStatus.NEW.value,
    )
    redeemed_at: Mapped[datetime.datetime | None] = mapped_column(sa.DateTime(timezone=True))
    redeemed_by_id: Mapped[str | None] = mapped_column(ForeignKey(FKEY_ORGANIZATION))
    redeemed_by: Mapped[Organization | None] = relationship(foreign_keys=[redeemed_by_id])

    terminated_at: Mapped[datetime.datetime | None] = mapped_column(sa.DateTime(timezone=True))
    terminated_by_id: Mapped[str | None] = mapped_column(ForeignKey(FKEY_ACTOR))
    terminated_by: Mapped[Actor | None] = relationship(foreign_keys=[terminated_by_id])

    redeem_at: Mapped[datetime.datetime | None] = mapped_column(sa.DateTime(timezone=True))


class ActivityLog(Base, HumanReadablePKMixin):
    __tablename__ = "activity_logs"

    PK_PREFIX = "FLOG"
    PK_NUM_LENGTH = 12

    # Named after the audit fields of `AuditableMixin` (`created_at` / `created_by`).
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC),
        server_default=sa.func.current_timestamp(),
        index=True,
    )
    recorded_by_id: Mapped[str] = mapped_column(
        ForeignKey(FKEY_ACTOR), name="recorded_by", nullable=False, index=True
    )
    recorded_by: Mapped[Actor] = relationship(foreign_keys=[recorded_by_id], lazy="raise")
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ActivityStatus.COMPLETED.value,
        server_default=ActivityStatus.COMPLETED.value,
    )
    # Identifies an operation (a multi-step / multi-attempt activity) so that every attempt
    # can find the entry of the operation it belongs to.
    operation_key: Mapped[str | None] = mapped_column(String(150), nullable=True)
    changes: Mapped[list[ChangeRecord]] = relationship(
        back_populates="activity_log",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
        order_by=lambda: (ChangeRecord.recorded_at, ChangeRecord.id),
    )
    notes: Mapped[list[ActivityNote]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
        order_by=lambda: (ActivityNote.recorded_at, ActivityNote.id),
    )

    __table_args__ = (
        # Only one entry per key can be in progress; finished entries can share a key.
        Index(
            "ux_activity_logs_operation_key_in_progress",
            operation_key,
            unique=True,
            postgresql_where=sa.text(f"status = '{ActivityStatus.IN_PROGRESS.value}'"),
        ),
    )


class ChangeRecord(Base):
    __tablename__ = "change_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # ty: ignore[invalid-attribute-override]
    activity_log_id: Mapped[str] = mapped_column(
        ForeignKey(FKEY_ACTIVITY_LOG, ondelete="CASCADE"), nullable=False, index=True
    )
    activity_log: Mapped[ActivityLog] = relationship(
        back_populates="changes", foreign_keys=[activity_log_id], lazy="raise"
    )
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    object_id: Mapped[str] = mapped_column(String(64), nullable=False)
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Orders the records of an entry when they are added by different attempts.
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.current_timestamp(),
    )

    __table_args__ = (Index("ix_change_records_object", object_type, object_id),)


class ActivityNote(Base):
    """A timestamped remark on an activity log entry, written by the actor of one attempt."""

    __tablename__ = "activity_notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # ty: ignore[invalid-attribute-override]
    activity_log_id: Mapped[str] = mapped_column(
        ForeignKey(FKEY_ACTIVITY_LOG, ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
    # `key` keeps the column reachable by its attribute name: inside `any(notes, ...)` requela
    # looks the column up by key, and `recorded_by` would resolve to the relationship.
    recorded_by_id: Mapped[str] = mapped_column(
        ForeignKey(FKEY_ACTOR),
        name="recorded_by",
        key="recorded_by_id",
        nullable=False,
        index=True,
    )
    recorded_by: Mapped[Actor] = relationship(foreign_keys=[recorded_by_id], lazy="raise")
    message: Mapped[str] = mapped_column(Text(), nullable=False)

    @hybrid_property
    def recorded_by_type(self) -> ActorType:
        """The type of the actor that recorded the note."""
        return self.recorded_by.type

    @recorded_by_type.inplace.expression
    @classmethod
    def _recorded_by_type_expression(cls) -> sa.Label[ActorType]:
        # Lets RQL filter on the actor's type inside `any(notes, ...)`, where requela cannot
        # follow the `recorded_by` relationship.
        # The `actors` table itself, not the `Actor` entity, which would also join the
        # tables of its subclasses.
        actors = Actor.__table__
        return (
            sa.select(actors.c.type)
            .where(actors.c.id == cls.recorded_by_id)
            .scalar_subquery()
            .label("recorded_by_type")
        )

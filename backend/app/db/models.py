"""
Project's ORM models module: defines database models such as
Account, Organization, Entitlement, etc.
"""

from __future__ import annotations

import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)

from app.db.human_readable_pk import HumanReadablePKMixin
from app.enums import (
    AccountStatus,
    AccountType,
    AccountUserStatus,
    ActorType,
    DatasourceType,
    EntitlementStatus,
    OrganizationStatus,
    SystemStatus,
    UserStatus,
)

FKEY_ORGANIZATION = "organizations.id"
FKEY_ACTOR = "actors.id"
FKEY_ACCOUNT = "accounts.id"
FKEY_USER = "users.id"


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

    __mapper_args__ = {
        "polymorphic_on": "type",
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
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=AccountStatus.ACTIVE,
        server_default=AccountStatus.ACTIVE.value,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    users: Mapped[list[AccountUser]] = relationship(back_populates="account")
    new_entitlements_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    active_entitlements_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    terminated_entitlements_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)

    @property
    def account_user(self) -> AccountUser | None:
        try:
            return self.users[0]
        except Exception:
            return None


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
    accounts: Mapped[list[AccountUser]] = relationship(back_populates="user", lazy="noload")

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

    __table_args__ = (
        Index(
            "ix_organizations_operations_external_id_for_non_deleted",
            operations_external_id,
            unique=True,
            postgresql_where=(status != OrganizationStatus.DELETED),
        ),
    )


class DatasourceExpense(Base, HumanReadablePKMixin, TimestampMixin):
    __tablename__ = "datasource_expenses"

    PK_PREFIX = "FDSX"
    PK_NUM_LENGTH = 12

    datasource_id: Mapped[str] = mapped_column(String(255), index=True)
    linked_datasource_id: Mapped[str] = mapped_column(String(255))
    linked_datasource_type: Mapped[DatasourceType] = mapped_column(
        Enum(DatasourceType, values_callable=lambda obj: [e.value for e in obj]),
    )
    datasource_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey(FKEY_ORGANIZATION))

    organization: Mapped[Organization] = relationship(lazy="noload", foreign_keys=[organization_id])

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


class AdditionalAdminRequest(Base, HumanReadablePKMixin, AuditableMixin):
    __tablename__ = "additionaladminrequests"
    PK_PREFIX = "FAAR"
    PK_NUM_LENGTH = 8

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str] = mapped_column(Text(), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey(FKEY_ORGANIZATION))
    organization: Mapped[Organization] = relationship(foreign_keys=[organization_id], lazy="joined")

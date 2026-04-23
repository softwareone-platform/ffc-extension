from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import sqlalchemy
from sqlalchemy import ColumnExpressionArgument, Select, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import ORMOption

from app.auth.context import auth_context
from app.db.models import (
    Account,
    AccountUser,
    AdditionalAdminRequest,
    AuditableMixin,
    DatasourceExpense,
    Entitlement,
    Organization,
    System,
    TimestampMixin,
    User,
)
from app.db.models import Base as BaseModel
from app.enums import (
    AccountUserStatus,
    EntitlementStatus,
)


class DatabaseError(Exception):
    pass


class NotFoundError(DatabaseError):
    pass


class CannotDeleteError(DatabaseError):
    pass


class ConstraintViolationError(DatabaseError):
    pass


class NullViolationError(DatabaseError):
    pass


class ModelHandler[M: BaseModel]:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.default_options: list[ORMOption] = []

    @classmethod
    def _get_generic_cls_args(cls):
        """
        Retrieves the generic model class arg dynamically
        """
        return next(
            base_cls.__args__
            for base_cls in cls.__orig_bases__
            if base_cls.__origin__ is ModelHandler
        )

    @property
    def model_cls(self) -> type[M]:
        return self._get_generic_cls_args()[0]

    async def create(self, obj: M) -> M:
        if isinstance(obj, AuditableMixin):  # pragma: no branch
            if obj.created_by is None:
                with suppress(LookupError):
                    obj.created_by = auth_context.get().get_actor()

            if obj.updated_by is None:
                with suppress(LookupError):
                    obj.updated_by = auth_context.get().get_actor()

        self.session.add(obj)
        await self._save_changes(obj)

        return obj

    async def get(
        self, id: str, extra_conditions: list[ColumnExpressionArgument] | None = None
    ) -> M:
        query = select(self.model_cls).where(self.model_cls.id == id)
        if extra_conditions:
            query = query.where(*extra_conditions)

        if self.default_options:
            query = query.options(*self.default_options)

        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if instance is None:
            raise NotFoundError(f"{self.model_cls.__name__} with ID `{str(id)}` wasn't found.")

        return instance

    async def get_or_create(
        self,
        *,
        defaults: dict[str, Any] | None = None,
        extra_conditions: list[ColumnExpressionArgument] | None = None,
        **filters: Any,
    ) -> tuple[M, bool]:
        defaults = defaults or {}
        query = select(self.model_cls).where(
            *(getattr(self.model_cls, key) == value for key, value in filters.items())
        )
        if extra_conditions:
            query = query.where(*extra_conditions)
        if self.default_options:
            query = query.options(*self.default_options)
        result = await self.session.execute(query)
        obj = result.scalars().first()

        if obj:
            return obj, False

        params = filters
        params.update(defaults)

        obj = await self.create(self.model_cls(**params))
        return obj, True

    async def update(self, id_or_obj: str | M, data: dict[str, Any] | None = None) -> M:
        obj = await self._get_model_obj(id_or_obj)

        if data:
            for key, value in data.items():
                setattr(obj, key, value)

        if (
            isinstance(obj, AuditableMixin) and data and "updated_by" not in data
        ):  # pragma: no branch
            with suppress(LookupError):
                obj.updated_by = auth_context.get().get_actor()

        await self._save_changes(obj)

        return obj

    async def delete(self, id_or_obj: str | M) -> M:
        obj = await self._get_model_obj(id_or_obj)

        model_inspection = sqlalchemy.inspect(obj.__class__)
        status_column = model_inspection.columns.get("status")

        if status_column is None:
            raise CannotDeleteError(f"{self.model_cls.__name__} does not have a status column.")

        if not isinstance(status_column.type, sqlalchemy.Enum):
            raise CannotDeleteError(f"{self.model_cls.__name__} status column is not an Enum.")

        if "deleted" not in status_column.type.enums:
            raise CannotDeleteError(
                f"{self.model_cls.__name__} status column does not have a 'deleted' value."
            )

        if obj.status == "deleted":  # type: ignore[attr-defined]
            raise CannotDeleteError(f"{self.model_cls.__name__} object is already deleted.")

        column_updates = {"status": "deleted"}

        if isinstance(obj, TimestampMixin):
            column_updates["deleted_at"] = datetime.now(UTC)

        if isinstance(obj, AuditableMixin):
            column_updates["updated_by"] = obj.updated_by
            with suppress(LookupError):
                column_updates["deleted_by"] = auth_context.get().get_actor()

        return await self.update(obj, data=column_updates)

    async def query_db(
        self,
        base_query: Select | None = None,
        where_clauses: Sequence[ColumnExpressionArgument] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: Sequence[ColumnExpressionArgument] | None = None,
        options: Sequence[ORMOption] | None = None,
        unique: bool = False,
    ) -> Sequence[M]:
        """
                Executes a database query with filtering, pagination, ordering, and options.

        This method allows for querying the database with conditions, applying additional
        filters, controlling pagination, ordering results, and enabling optional query options.

        Args:

            where_clauses (Sequence[ColumnExpressionArgument | Exists] | None, optional):
                - Additional conditions applied using `.where()`.
                - Useful for combining multiple filters dynamically.
                - Default is `None`.

            limit (int | None, optional):
                - Maximum number of results to return.
                - If `None`, retrieves all results.
                - Default is `50`.

            offset (int, optional):
                - Number of records to skip for pagination.
                - Default is `0`.


            order_by (str | None, optional):
                - Column name used to order the results.
                - Default is `"id"`.

            options (list[ORMOption] | None, optional):
                - SQLAlchemy ORM options to modify query behavior
                (e.g., `joinedload` for relationships).
                - Default is `None`.

            unique: Boolean (`True`) or `False` (`False`).
        Returns:
            Sequence[M]:
                - A list of objects matching the query.
                - If no records are found, returns an empty list.

        """
        # default query
        query = select(self.model_cls) if base_query is None else base_query
        # add the default options, if any
        query = self._apply_conditions_to_the_query(
            query=query, where_clauses=where_clauses, options=options, order_by=order_by
        )
        if limit:
            # apply limit
            query = query.limit(limit)
        if offset:
            # apply offset
            query = query.offset(offset)
        results = await self.session.scalars(query)
        if unique:
            return results.unique().all()
        return results.all()

    async def stream_scalars(
        self,
        extra_conditions: list[ColumnExpressionArgument] | None = None,
        order_by: list[ColumnExpressionArgument] | None = None,
        batch_size: int = 100,
    ) -> AsyncGenerator[M, None]:
        query = select(self.model_cls)
        query = self._apply_conditions_to_the_query(
            query=query, where_clauses=extra_conditions, order_by=order_by
        )
        result = await self.session.stream_scalars(
            query,
            execution_options={"yield_per": batch_size},
        )
        async for row in result:
            yield row
        await result.close()

    async def count(
        self,
        base_query: Select | None = None,
        where_clauses: Sequence[ColumnExpressionArgument] | None = None,
    ) -> int:
        """
        Counts the number of objects matching the given conditions.

        Args:
            *where_clauses (ColumnExpressionArgument): Filtering conditions.

        Returns:
            int: The count of matching records.
        """
        if base_query is not None:
            query = select(func.count(self.model_cls.id)).select_from(
                base_query.get_final_froms()[0]
            )
            if base_query.whereclause is not None:
                query = query.where(base_query.whereclause)
        else:
            query = select(func.count(self.model_cls.id))
        if where_clauses:
            query = query.where(*where_clauses)
        result = await self.session.execute(query)
        return result.scalars().one()

    async def first(
        self,
        base_query: Select | None = None,
        where_clauses: Sequence[ColumnExpressionArgument] | None = None,
    ) -> M | None:
        query = select(self.model_cls) if base_query is None else base_query
        query = self._apply_conditions_to_the_query(query=query, where_clauses=where_clauses)

        result = await self.session.execute(query)
        return result.scalars().first()

    async def _get_model_obj(self, id_or_obj: str | M) -> M:
        if isinstance(id_or_obj, str):
            return await self.get(id_or_obj)

        return id_or_obj

    async def _save_changes(self, obj: M):
        try:
            await self.session.flush()
        except IntegrityError as e:
            raise ConstraintViolationError(
                f"Failed to save changes to {self.model_cls.__name__}: {e}."
            ) from e
        await self.session.refresh(obj)

    def _apply_conditions_to_the_query(
        self,
        query: Select,
        where_clauses: Sequence[ColumnExpressionArgument] | None = None,
        options: Sequence[ORMOption] | None = None,
        order_by: Sequence[ColumnExpressionArgument] | None = None,
    ) -> Select:
        """
        Applies default options and extra conditions to the query.

        Args:
            query (Select): The query to modify.
            where_clauses (list[ColumnExpressionArgument] | None): Additional query conditions.

        Returns:
            Select: The modified query.
        """
        if where_clauses:
            query = query.where(*where_clauses)
        orm_options = (list(self.default_options) or []) + (list(options or []))
        if order_by:
            query = query.order_by(*order_by)
        if orm_options:
            query = query.options(*orm_options)
        return query


class EntitlementHandler(ModelHandler[Entitlement]):
    """
    Handles CRUD operations for the Entitlement model.
    """

    def __init__(self, session):
        super().__init__(session)
        self.default_options = [
            joinedload(Entitlement.owner),
            joinedload(Entitlement.created_by),
            joinedload(Entitlement.updated_by),
            joinedload(Entitlement.redeemed_by),
        ]

    async def terminate(self, entitlement: Entitlement) -> Entitlement:
        return await self.update(
            entitlement,
            data={
                "status": EntitlementStatus.TERMINATED,
                "terminated_at": datetime.now(UTC),
                "terminated_by": auth_context.get().get_actor(),
            },
        )

    async def get_stats_by_account(self, account_id: str) -> dict[str, Any]:
        """
        Fetches and counts all the Entitlement statues different from DELETED that are linked to the
        given account_id.
        Returns : a dict like
        {<EntitlementStatus.NEW: 'new'>: 15, <EntitlementStatus.ACTIVE: 'active'>: 30,
        <EntitlementStatus.TERMINATED: 'terminated'>: 7}
        """
        stmt = (
            select(Entitlement.status, func.count(Entitlement.id))
            .where(
                Entitlement.owner_id == account_id, Entitlement.status != EntitlementStatus.DELETED
            )
            .group_by(Entitlement.status)
        )

        response = await self.session.execute(stmt)
        return dict(list(response.tuples()))

    async def redeem(
        self,
        entitlement: Entitlement,
        redeemer_organization: Organization,
        datasource_id: UUID | str,
        datasource_name: str,
        datasource_type: str,
    ) -> Entitlement:
        return await self.update(
            entitlement,
            data={
                "status": EntitlementStatus.ACTIVE,
                "redeemed_at": entitlement.redeem_at or datetime.now(UTC),
                "redeemed_by": redeemer_organization,
                "linked_datasource_id": str(datasource_id),
                "linked_datasource_type": datasource_type,
                "linked_datasource_name": datasource_name,
            },
        )

    async def get_for_billing(
        self,
        organization_id: str,
        datasource_id: str,
        datasource_type: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Entitlement | None:
        where_clauses = [
            Entitlement.datasource_id == datasource_id,
            Entitlement.redeemed_by_id == organization_id,
            Entitlement.linked_datasource_type == datasource_type,
            Entitlement.redeemed_at < (end_date + timedelta(days=1)),
            or_(
                Entitlement.status == EntitlementStatus.ACTIVE,
                Entitlement.terminated_at >= start_date,
            ),
        ]

        return await self.first(where_clauses=where_clauses)


class OrganizationHandler(ModelHandler[Organization]):
    """
    Handles CRUD operations for the Organization model.
    """

    async def get_by_billing_currency(
        self,
        billing_currency: str,
    ) -> AsyncGenerator[Organization, None]:
        where_clauses = [Organization.billing_currency == billing_currency]

        async for organization in self.stream_scalars(extra_conditions=where_clauses):
            yield organization


class SystemHandler(ModelHandler[System]):
    """
    Handles CRUD operations for the System model.
    """

    def __init__(self, session):
        super().__init__(session)
        self.default_options = [
            joinedload(System.owner),
            joinedload(System.created_by),
            joinedload(System.updated_by),
            joinedload(System.deleted_by),
        ]


class AccountHandler(ModelHandler[Account]):
    """
    Handles CRUD operations for the Account model.
    """

    def __init__(self, session):
        super().__init__(session)
        self.default_options = [
            joinedload(Account.created_by),
            joinedload(Account.updated_by),
            joinedload(Account.deleted_by),
        ]


class UserHandler(ModelHandler[User]):
    """
    Handles CRUD operations for the User model.
    """

    def __init__(self, session):
        super().__init__(session)
        self.default_options = [
            joinedload(User.created_by),
            joinedload(User.updated_by),
            joinedload(User.deleted_by),
        ]


class AccountUserHandler(ModelHandler[AccountUser]):
    """
    Handles CRUD operations for the AccountUser model.
    """

    def __init__(self, session):
        super().__init__(session)
        self.default_options = [
            joinedload(AccountUser.account),
            joinedload(AccountUser.user),
        ]

    async def delete_by_user(self, user_id: str):
        """
        Updates the status of the AccountUser that belongs to the user
        identified by the given user_id, to DELETE.
        """
        actor_obj = auth_context.get().get_actor() if auth_context.get() else None
        actor_id = getattr(actor_obj, "id", None)
        stmt = (
            update(AccountUser)
            .where(AccountUser.status != AccountUserStatus.DELETED, AccountUser.user_id == user_id)
            .values(
                status=AccountUserStatus.DELETED,
                deleted_at=datetime.now(UTC),
                deleted_by_id=actor_id,
                # Explicitly set the relationship key
                # value instead of setting the expected `deleted_at` field. Setting the deleted_by
                # causes an error due to a misinterpreted query that puts the deleted_at field
                # expecting a boolean value
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_account_user(
        self,
        account_id: str,
        user_id: str,
        extra_conditions: list[ColumnExpressionArgument] | None = None,
    ) -> AccountUser | None:
        query = select(self.model_cls).where(
            self.model_cls.account_id == account_id,
            self.model_cls.user_id == user_id,
        )
        if extra_conditions:
            query = query.where(*extra_conditions)
        if self.default_options:
            query = query.options(*self.default_options)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class DatasourceExpenseHandler(ModelHandler[DatasourceExpense]):
    """
    Handles CRUD operations for the DatasourceExpense model.
    """

    def __init__(self, session):
        super().__init__(session)
        self.default_options = [
            joinedload(DatasourceExpense.organization),
        ]

    async def get_expenses_for_billing(
        self,
        organization_id: str,
        year: int,
        month: int,
    ) -> AsyncGenerator[DatasourceExpense, None]:
        where_clauses = [
            DatasourceExpense.organization_id == organization_id,
            DatasourceExpense.year == year,
            DatasourceExpense.month == month,
        ]
        order_by = [
            DatasourceExpense.linked_datasource_id,
            DatasourceExpense.linked_datasource_type,
            DatasourceExpense.datasource_id,
            DatasourceExpense.datasource_name,
            DatasourceExpense.day,
        ]
        async for expense in self.stream_scalars(
            extra_conditions=where_clauses,
            order_by=order_by,
        ):
            yield expense


class AdditionalAdminRequestHandler(ModelHandler[AdditionalAdminRequest]):
    pass

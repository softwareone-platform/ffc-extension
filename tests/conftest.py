import inspect
import secrets
import uuid
from collections.abc import AsyncGenerator, Callable, Generator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from asgi_lifespan import LifespanManager
from faker import Faker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pytest_asyncio import is_async_test
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
)

from app.conf import Settings, get_settings
from app.db.base import configure_db_engine, session_factory
from app.db.models import (
    Account,
    AccountUser,
    Actor,
    Base,
    DatasourceExpense,
    Entitlement,
    Organization,
    System,
    User,
)
from app.enums import (
    AccountStatus,
    AccountType,
    AccountUserStatus,
    DatasourceType,
    EntitlementStatus,
    OrganizationStatus,
    SystemStatus,
    UserStatus,
)
from tests.db.models import ModelForTests, ParentModelForTests  # noqa: F401
from tests.types import ModelFactory

pytest_plugins = [
    "tests.fixtures.mock_api_clients",
]


@pytest.fixture(scope="session", autouse=True)
def skip_logging_setup() -> Generator:
    from unittest.mock import patch

    with patch("app.cli.setup_logging"):
        yield


def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    settings = Settings(
        _env_file=("../.env", "../.env.test"),
        _env_file_encoding="utf-8",
    )
    settings.optscale_cluster_secret = "test_cluster_secret"
    settings.optscale_rest_api_base_url = "https://opt-api.ffc.com"
    settings.optscale_auth_api_base_url = "https://opt-auth.ffc.com"
    settings.api_modifier_base_url = "https://api-modifier.ffc.com"
    settings.api_modifier_jwt_secret = "test_jwt_secrettest_jwt_secrettest_jwt_secretpyt"
    settings.opentelemetry_exporter = None
    settings.smtp_sender_email = "test@example.com"
    settings.smtp_sender_name = "Test Sender"
    settings.smtp_host = "smtp.example.com"
    settings.smtp_port = 587
    settings.smtp_user = "user"
    settings.smtp_password = "password"
    settings.cli_rich_logging = False
    settings.msteams_notifications_webhook_url = "https://example.com/webhook"
    return settings


@pytest.fixture(scope="session")
def db_engine(test_settings: Settings) -> AsyncEngine:
    return configure_db_engine(test_settings)


@pytest.fixture(scope="session", autouse=True)
async def setup_db_tables(db_engine: AsyncEngine) -> AsyncGenerator[None]:
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield
    finally:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await db_engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    # Use nested transactions to avoid committing changes to the database, speeding up
    # the tests significantly and avoiding side effects between them.
    #
    # ref: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites

    async with db_engine.connect() as conn:
        outer_transaction = await conn.begin()
        session_factory.configure(bind=conn, join_transaction_mode="create_savepoint")

        try:
            async with session_factory() as s:
                yield s
        finally:
            await outer_transaction.rollback()


@pytest.fixture(scope="session")
def fastapi_app(test_settings: Settings) -> FastAPI:
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: test_settings
    return app


@pytest.fixture(scope="session")
async def app_lifespan_manager(fastapi_app: FastAPI) -> AsyncGenerator[LifespanManager, None]:
    async with LifespanManager(fastapi_app) as lifespan_manager:
        yield lifespan_manager


@pytest.fixture
async def api_client(
    app_lifespan_manager: LifespanManager,
) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app_lifespan_manager.app),
        base_url="http://localhost/ops/v1",
    ) as client:
        yield client


@pytest.fixture
def account_factory(faker: Faker, db_session: AsyncSession) -> ModelFactory[Account]:
    async def _account(
        name: str | None = None,
        type: str | None = None,
        external_id: str | None = None,
        status: AccountStatus | None = None,
        created_by: Actor | None = None,
        updated_by: Actor | None = None,
        new_entitlements_count: int = 0,
        active_entitlements_count: int = 0,
        terminated_entitlements_count: int = 0,
    ) -> Account:
        account = Account(
            type=type or AccountType.AFFILIATE,
            name=name or "AWS",
            external_id=external_id or str(faker.uuid4()),
            status=status or AccountStatus.ACTIVE,
            created_by=created_by,
            updated_by=updated_by,
            new_entitlements_count=new_entitlements_count,
            active_entitlements_count=active_entitlements_count,
            terminated_entitlements_count=terminated_entitlements_count,
        )
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)
        return account

    return _account


@pytest.fixture
def entitlement_factory(
    faker: Faker,
    db_session: AsyncSession,
    account_factory: ModelFactory[Account],
) -> ModelFactory[Entitlement]:
    async def _entitlement(
        name: str | None = None,
        affiliate_external_id: str | None = None,
        datasource_id: str | None = None,
        linked_datasource_id: str | None = None,
        linked_datasource_type: DatasourceType | None = None,
        created_by: Actor | None = None,
        updated_by: Actor | None = None,
        owner: Account | None = None,
        status: EntitlementStatus | None = None,
        redeem_at: datetime | None = None,
    ) -> Entitlement:
        entitlement = Entitlement(
            name=name or "AWS",
            affiliate_external_id=affiliate_external_id or "ACC-1234-5678",
            datasource_id=datasource_id or faker.uuid4(),
            linked_datasource_id=linked_datasource_id,
            linked_datasource_type=linked_datasource_type,
            created_by=created_by,
            updated_by=updated_by,
            status=status or EntitlementStatus.NEW,
            owner=owner or await account_factory(),
            redeem_at=redeem_at,
        )
        db_session.add(entitlement)
        await db_session.commit()
        await db_session.refresh(entitlement)
        return entitlement

    return _entitlement


@pytest.fixture
def organization_factory(faker: Faker, db_session: AsyncSession) -> ModelFactory[Organization]:
    async def _organization(
        name: str | None = None,
        currency: str | None = None,
        billing_currency: str | None = None,
        operations_external_id: str | None = None,
        linked_organization_id: str | None = None,
        created_by: Actor | None = None,
        updated_by: Actor | None = None,
        status: OrganizationStatus = OrganizationStatus.ACTIVE,
    ) -> Organization:
        organization = Organization(
            name=name or faker.company(),
            currency=currency or "EUR",
            billing_currency=billing_currency or "USD",
            operations_external_id=operations_external_id or "AGR-1234-5678-9012",
            linked_organization_id=linked_organization_id,
            created_by=created_by,
            updated_by=updated_by,
            status=status,
        )
        db_session.add(organization)
        await db_session.commit()
        await db_session.refresh(organization)
        return organization

    return _organization


@pytest.fixture
def system_factory(
    faker: Faker, db_session: AsyncSession, account_factory: ModelFactory[Account]
) -> ModelFactory[System]:
    async def _system(
        name: str | None = None,
        external_id: str | None = None,
        owner: Account | None = None,
        status: SystemStatus = SystemStatus.ACTIVE,
    ) -> System:
        owner = owner or await account_factory()
        system = System(
            name=name or faker.company(),
            external_id=external_id or str(uuid.uuid4()),
            owner=owner or await account_factory(),
            status=status,
        )
        db_session.add(system)
        await db_session.commit()
        await db_session.refresh(system)
        return system

    return _system


@pytest.fixture
def accountuser_factory(db_session: AsyncSession):
    async def _accountuser(
        user_id: str,
        account_id: str,
        status: AccountUserStatus = AccountUserStatus.ACTIVE,
    ) -> AccountUser:
        account_user = AccountUser(
            user_id=user_id,
            account_id=account_id,
            status=status,
        )
        db_session.add(account_user)
        await db_session.commit()
        await db_session.refresh(account_user)
        return account_user

    return _accountuser


@pytest.fixture
def user_factory(
    faker: Faker, db_session: AsyncSession, account_factory: ModelFactory[Account]
) -> ModelFactory[User]:
    async def _user(
        name: str | None = None,
        email: str | None = None,
        status: UserStatus = UserStatus.ACTIVE,
        account: Account | None = None,
        accountuser_status: AccountUserStatus = AccountUserStatus.ACTIVE,
    ) -> User:
        account = account or await account_factory()
        user = User(
            name=name or faker.name(),
            email=email or faker.email(),
            status=status,
        )

        db_session.add(user)
        account_user = AccountUser(
            user=user,
            account=account or await account_factory(),
            status=accountuser_status,
        )
        db_session.add(account_user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _user


@pytest.fixture
def jwt_token_factory() -> Callable[
    [str, str, str | None, str | None, datetime | None, datetime | None, datetime | None], str
]:
    def _jwt_token(
        account_id: str = "ACC-1111-2222",
        account_type: str = "Vendor",
        user_id: str | None = "USR-0000-1111",
        token_id: str | None = None,
        exp: datetime | None = None,
        nbf: datetime | None = None,
        iat: datetime | None = None,
    ) -> str:
        now = datetime.now(UTC)
        claims = {
            "https://claims.softwareone.com/accountId": account_id,
            "https://claims.softwareone.com/accountType": account_type,
            "https://claims.softwareone.com/userId": user_id,
            "https://claims.softwareone.com/apiTokenId": token_id,
            "https://claims.softwareone.com/installationId": "EXI-0000-1111-2222",
            "iat": iat or now,
            "nbf": nbf or now,
            "exp": exp or now + timedelta(minutes=5),
        }
        if account_id:
            claims["account_id"] = account_id

        return jwt.encode(
            claims,
            secrets.token_hex(16),
            algorithm="HS256",
        )

    return _jwt_token


@pytest.fixture
def system_jwt_token_factory(
    jwt_token_factory,
) -> Callable[[System], str]:
    def _system_jwt_token(system: System) -> str:
        now = datetime.now(UTC)

        return jwt_token_factory(
            account_id=str(system.owner.external_id),
            user_id=None,
            token_id=system.external_id,
            exp=now + timedelta(minutes=5),
            nbf=now,
            iat=now,
        )

    return _system_jwt_token


@pytest.fixture
def datasource_expense_factory(
    faker: Faker,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
) -> ModelFactory[DatasourceExpense]:
    async def _datasource_expense(
        organization: Organization | None = None,
        year: int = 2025,
        month: int = 3,
        day: int = 1,
        total_expenses: float = 34567.89,
        expenses: float | None = None,
        datasource_id: str | None = None,
        linked_datasource_id: str | None = None,
        linked_datasource_type: DatasourceType | None = None,
        datasource_name: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> DatasourceExpense:
        organization = organization or await organization_factory()

        datasource_expense = DatasourceExpense(
            organization=organization,
            datasource_id=datasource_id or faker.uuid4(),
            linked_datasource_id=linked_datasource_id or faker.uuid4(),
            linked_datasource_type=linked_datasource_type or DatasourceType.AWS_CNR,
            datasource_name=datasource_name or "Datasource Name",
            year=year,
            month=month,
            day=day,
            expenses=expenses,
            total_expenses=total_expenses,
            created_at=created_at or datetime.now(UTC) - timedelta(days=7),
            updated_at=updated_at or datetime.now(UTC) - timedelta(days=7),
        )
        db_session.add(datasource_expense)
        await db_session.commit()
        await db_session.refresh(datasource_expense)
        return datasource_expense

    return _datasource_expense


@pytest.fixture
async def aws_account(account_factory: ModelFactory[Account]) -> Account:
    return await account_factory(
        name="AWS", type=AccountType.AFFILIATE, external_id="ACC-2222-2222"
    )


@pytest.fixture
async def gcp_account(account_factory: ModelFactory[Account]) -> Account:
    return await account_factory(
        name="GCP",
        type=AccountType.AFFILIATE,
        external_id="ACC-1111-1111",
    )


@pytest.fixture
async def gcp_extension(system_factory: ModelFactory[System], gcp_account: Account) -> System:
    return await system_factory(external_id="TKN-1111-1111", owner=gcp_account)


@pytest.fixture
async def aws_extension(system_factory: ModelFactory[System], aws_account: Account) -> System:
    return await system_factory(external_id="TKN-2222-2222", owner=aws_account)


@pytest.fixture
async def operations_account(account_factory: ModelFactory[Account]) -> Account:
    return await account_factory(
        name="SoftwareOne", type=AccountType.OPERATIONS, external_id="ACC-0000-0000"
    )


@pytest.fixture
async def affiliate_account(
    account_factory: ModelFactory[Account], ffc_extension: System
) -> Account:
    return await account_factory(
        name="Microsoft",
        type=AccountType.AFFILIATE,
        created_by=ffc_extension,
        updated_by=ffc_extension,
        new_entitlements_count=10,
        active_entitlements_count=15,
        terminated_entitlements_count=50,
        external_id="ACC-3333-3333",
    )


@pytest.fixture
async def affiliate_system(
    system_factory: ModelFactory[System], affiliate_account: Account
) -> System:
    return await system_factory(external_id="TKN-3333-3333", owner=affiliate_account)


@pytest.fixture
def affiliate_account_jwt_token(
    system_jwt_token_factory: Callable[[System], str], affiliate_system: System
) -> str:
    return system_jwt_token_factory(affiliate_system)


@pytest.fixture
def gcp_jwt_token(system_jwt_token_factory: Callable[[System], str], gcp_extension: System) -> str:
    return system_jwt_token_factory(gcp_extension)


@pytest.fixture
async def ffc_extension(
    system_factory: ModelFactory[System], operations_account: Account
) -> System:
    return await system_factory(external_id="TKN-0000-0000", owner=operations_account)


@pytest.fixture
def ffc_jwt_token(system_jwt_token_factory: Callable[[System], str], ffc_extension: System) -> str:
    return system_jwt_token_factory(ffc_extension)


@pytest.fixture
async def entitlement_aws(
    entitlement_factory: ModelFactory[Entitlement], aws_extension: System
) -> Entitlement:
    return await entitlement_factory(
        name="AWS",
        owner=aws_extension.owner,
        created_by=aws_extension,
        updated_by=aws_extension,
    )


@pytest.fixture
async def entitlement_gcp(
    entitlement_factory: ModelFactory[Entitlement],
    gcp_extension: System,
) -> Entitlement:
    return await entitlement_factory(
        name="GCP",
        owner=gcp_extension.owner,
        created_by=gcp_extension,
        updated_by=gcp_extension,
    )


@pytest.fixture
async def entitlement_gcp_with_redeem_at(
    entitlement_factory: ModelFactory[Entitlement],
    gcp_extension: System,
) -> Entitlement:
    return await entitlement_factory(
        name="GCP",
        owner=gcp_extension.owner,
        created_by=gcp_extension,
        updated_by=gcp_extension,
        redeem_at=datetime.now(UTC) - timedelta(days=1),
    )


@pytest.fixture
def affiliate_client(api_client: AsyncClient, gcp_jwt_token: str) -> AsyncClient:
    api_client.headers["Authorization"] = f"Bearer {gcp_jwt_token}"
    return api_client


@pytest.fixture
def operations_client(api_client: AsyncClient, ffc_jwt_token: str) -> AsyncClient:
    api_client.headers["Authorization"] = f"Bearer {ffc_jwt_token}"
    return api_client


@pytest.fixture
async def apple_inc_organization(organization_factory: ModelFactory[Organization]) -> Organization:
    return await organization_factory(
        name="Apple Inc.",
        currency="USD",
        linked_organization_id=str(uuid.uuid4()),
    )


def assert_equal_or_raises[T](
    func: Callable[[], T],
    expected: T | type[Exception] | Exception,
) -> None:
    """Assert that an expression either returns a specific value or raises an exception.

    Especially useful when used with `pytest.mark.parametrize` to check different scenarios.

    Example Usage:

    ```python
    @pytest.mark.parametrize(
        ("numerator", "denominator", "expected"),
        [
            (5, 2, 2.5),
            (2, 2, 1.0),
            (1, 0, ZeroDivisionError("division by zero")),
            (1, "string", TypeError),
        ],
    )
    def test_division(numerator, denominator, expected):
        assert_equal_or_raises(lambda: numerator / denominator, expected)
    ```
    """

    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            func()
    elif isinstance(expected, Exception):
        with pytest.raises(expected.__class__, match=str(expected)):
            func()
    else:
        assert func() == expected

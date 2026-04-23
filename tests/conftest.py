import inspect
import secrets
import tempfile
import uuid
from collections.abc import AsyncGenerator, Callable, Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx
import jwt
import pytest
import responses
from asgi_lifespan import LifespanManager
from faker import Faker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pytest_asyncio import is_async_test
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
)

from app.api_clients.base import BaseAPIClient
from app.billing.dataclasses import ProcessResultInfo
from app.billing.enum import ProcessResult
from app.billing.process_billing import AuthorizationProcessor
from app.conf import Settings, get_settings
from app.db.base import configure_db_engine, session_factory
from app.db.models import (
    Account,
    AccountUser,
    Actor,
    ActorType,
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
async def build_test_organization(organization_factory):
    organization_data = await organization_factory(
        name="SoftwareOne (Test Environment)",
        currency="USD",
        billing_currency="EUR",
        operations_external_id="ACC-1234-5678",
        linked_organization_id="3d0fe384-b1cf-4929-ad5e-1aa544f93dd5",
        status=OrganizationStatus.ACTIVE,
    )
    organization_data.id = "FORG-4801-6958-2949"
    return organization_data


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
        total_expenses: Decimal = Decimal(34567.89),
        expenses: Decimal | None = None,
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
async def admin_account(account_factory: ModelFactory[Account]) -> Account:
    return await account_factory(
        name="SoftwareOne", type=AccountType.ADMIN, external_id="ACC-0000-0000"
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
async def ffc_extension(system_factory: ModelFactory[System], admin_account: Account) -> System:
    return await system_factory(external_id="TKN-0000-0000", owner=admin_account)


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
def admin_client(api_client: AsyncClient, ffc_jwt_token: str) -> AsyncClient:
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


# ---------


@pytest.fixture()
def requests_mocker():
    """
    Allow mocking of http calls made with requests.
    """
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture()
def get_organizations():
    creator = Actor(
        id="FUSR-6956-9254",
        name="FrancescoFaraone",
        type=ActorType.USER,
        external_id="FUSR-6956-9254",
    )
    return Organization(
        name="SoftwareOne (Test Environment)",
        currency="USD",
        billing_currency="EUR",
        operations_external_id="ACC-1234-5678",
        id="FORG-4801-6958-2949",
        linked_organization_id="3d0fe384-b1cf-4929-ad5e-1aa544f93dd5",
        status=OrganizationStatus.ACTIVE,
        created_at=datetime(2025, 4, 3, 15, 18, 2, 408803, tzinfo=UTC),
        created_by_id="FUSR-6956-9254",
        created_by=creator,
        updated_at=datetime(2025, 4, 22, 13, 32, 0, 599322, tzinfo=UTC),
        updated_by_id="FUSR-6956-9254",
        updated_by=creator,
    )


@pytest.fixture()
def order_parameters_factory():
    def _order_parameters():
        return [
            {
                "id": "PAR-7208-0459-0004",
                "externalId": "organizationName",
                "name": "Organization Name",
                "type": "SingleLineText",
                "phase": "Order",
                "displayValue": "ACME Inc",
                "value": "ACME Inc",
            },
            {
                "id": "PAR-7208-0459-0005",
                "externalId": "adminContact",
                "name": "Administrator",
                "type": "Contact",
                "phase": "Order",
                "displayValue": "PL NN pl@example.com",
                "value": {
                    "firstName": "PL",
                    "lastName": "NN",
                    "email": "pl@example.com",
                    "phone": None,
                },
            },
            {
                "id": "PAR-7208-0459-0006",
                "externalId": "currency",
                "name": "Currency",
                "type": "DropDown",
                "phase": "Order",
                "displayValue": "USD",
                "value": "USD",
            },
        ]

    return _order_parameters


@pytest.fixture()
def fulfillment_parameters_factory():
    def _fulfillment_parameters():
        return [
            {
                "id": "PAR-7208-0459-0007",
                "externalId": "dueDate",
                "name": "Due Date",
                "type": "Date",
                "phase": "Fulfillment",
                "value": "2025-01-01",
            },
            {
                "id": "PAR-7208-0459-0008",
                "externalId": "isNewUser",
                "name": "Is New User?",
                "type": "Checkbox",
                "phase": "Fulfillment",
            },
            {
                "id": "PAR-7208-0459-0009",
                "externalId": "trialStartDate",
                "name": "Trial Start Date",
                "type": "Date",
                "phase": "Fulfillment",
                "value": "2025-01-01",
            },
            {
                "id": "PAR-7208-0459-0010",
                "externalId": "trialEndDate",
                "name": "Trial Start Date",
                "type": "Date",
                "phase": "Fulfillment",
                "value": "2025-01-31",
            },
            {
                "id": "PAR-7208-0459-0011",
                "externalId": "billedPercentage",
                "name": "Billed Percentage",
                "type": "SingleLineText",
                "phase": "Fulfillment",
                "value": "4",
            },
        ]

    return _fulfillment_parameters


@pytest.fixture()
def items_factory():
    def _items(
        item_id=1,
        name="Awesome product",
        external_vendor_id="FINOPS-ITEM-00001",
    ):
        return [
            {
                "id": f"ITM-1234-1234-1234-{item_id:04d}",
                "name": name,
                "externalIds": {
                    "vendor": external_vendor_id,
                },
            },
        ]

    return _items


@pytest.fixture()
def lines_factory(agreement):
    agreement_id = agreement["id"].split("-", 1)[1]

    def _items(
        line_id=1,
        item_id=1,
        name="Awesome product",
        old_quantity=0,
        quantity=170,
        external_vendor_id="FINOPS-ITEM-00001",
        unit_purchase_price=1234.55,
    ):
        line = {
            "item": {
                "id": f"ITM-1234-1234-1234-{item_id:04d}",
                "name": name,
                "externalIds": {
                    "vendor": external_vendor_id,
                },
            },
            "oldQuantity": old_quantity,
            "quantity": quantity,
            "price": {
                "unitPP": unit_purchase_price,
            },
        }
        if line_id:
            line["id"] = f"ALI-{agreement_id}-{line_id:04d}"
        return [line]

    return _items


@pytest.fixture()
def subscriptions_factory(lines_factory):
    def _subscriptions(
        subscription_id="SUB-1000-2000-3000",
        product_name="Awesome product",
        vendor_id="123-456-789",
        start_date=None,
        commitment_date=None,
        lines=None,
    ):
        start_date = start_date.isoformat() if start_date else datetime.now(UTC).isoformat()
        lines = lines_factory() if lines is None else lines
        return [
            {
                "id": subscription_id,
                "name": f"Subscription for {product_name}",
                "parameters": {"fulfillment": [{}]},
                "externalIds": {
                    "vendor": vendor_id,
                },
                "lines": lines,
                "startDate": start_date,
                "commitmentDate": commitment_date,
            }
        ]

    return _subscriptions


@pytest.fixture()
def agreement_factory(buyer, order_parameters_factory, fulfillment_parameters_factory):
    def _agreement(
        licensee_name="My beautiful licensee",
        licensee_address=None,
        licensee_contact=None,
        use_buyer_address=False,
        subscriptions=None,
        fulfillment_parameters=None,
        ordering_parameters=None,
        lines=None,
    ):
        if not subscriptions:
            subscriptions = [
                {
                    "id": "SUB-1000-2000-3000",
                    "status": "Active",
                    "item": {
                        "id": "ITM-0000-0001-0001",
                    },
                },
                {
                    "id": "SUB-1234-5678",
                    "status": "Terminated",
                    "item": {
                        "id": "ITM-0000-0001-0002",
                    },
                },
            ]

        licensee = {
            "name": licensee_name,
            "address": licensee_address,
            "useBuyerAddress": use_buyer_address,
        }
        if licensee_contact:
            licensee["contact"] = licensee_contact

        return {
            "id": "AGR-2119-4550-8674-5962",
            "href": "/commerce/agreements/AGR-2119-4550-8674-5962",
            "icon": None,
            "name": "Product Name 1",
            "audit": {
                "created": {
                    "at": "2023-12-14T18:02:16.9359",
                    "by": {"id": "USR-0000-0001"},
                },
                "updated": None,
            },
            "listing": {
                "id": "LST-9401-9279",
                "href": "/listing/LST-9401-9279",
                "priceList": {
                    "id": "PRC-9457-4272-3691",
                    "href": "/v1/price-lists/PRC-9457-4272-3691",
                    "currency": "USD",
                },
            },
            "licensee": licensee,
            "buyer": buyer,
            "seller": {
                "id": "SEL-9121-8944",
                "href": "/accounts/sellers/SEL-9121-8944",
                "name": "Software LN",
                "icon": "/static/SEL-9121-8944/icon.png",
                "address": {
                    "country": "US",
                },
            },
            "client": {
                "id": "ACC-9121-8944",
                "href": "/accounts/sellers/ACC-9121-8944",
                "name": "Software LN",
                "icon": "/static/ACC-9121-8944/icon.png",
            },
            "product": {
                "id": "PRD-1111-1111",
            },
            "authorization": {"id": "AUT-1234-5678"},
            "lines": lines or [],
            "subscriptions": subscriptions,
            "parameters": {
                "ordering": ordering_parameters or order_parameters_factory(),
                "fulfillment": fulfillment_parameters or fulfillment_parameters_factory(),
            },
        }

    return _agreement


@pytest.fixture()
def licensee(buyer):
    return {
        "id": "LCE-1111-2222-3333",
        "name": "FF Buyer good enough",
        "useBuyerAddress": True,
        "address": buyer["address"],
        "contact": buyer["contact"],
        "buyer": buyer,
        "account": {
            "id": "ACC-1234-1234",
            "name": "Client Account",
        },
    }


@pytest.fixture()
def listing(buyer):
    return {
        "id": "LST-9401-9279",
        "href": "/listing/LST-9401-9279",
        "priceList": {
            "id": "PRC-9457-4272-3691",
            "href": "/v1/price-lists/PRC-9457-4272-3691",
            "currency": "USD",
        },
        "product": {
            "id": "PRD-1234-1234",
            "name": "Product Name",
        },
        "vendor": {
            "id": "ACC-1234-vendor-id",
            "name": "Vendor Name",
        },
    }


@pytest.fixture()
def buyer():
    return {
        "id": "BUY-3731-7971",
        "href": "/accounts/buyers/BUY-3731-7971",
        "name": "A buyer",
        "icon": "/static/BUY-3731-7971/icon.png",
        "address": {
            "country": "US",
            "state": "CA",
            "city": "San Jose",
            "addressLine1": "3601 Lyon St",
            "addressLine2": "",
            "postCode": "94123",
        },
        "contact": {
            "firstName": "Cic",
            "lastName": "Faraone",
            "email": "francesco.faraone@softwareone.com",
            "phone": {
                "prefix": "+1",
                "number": "4082954078",
            },
        },
    }


@pytest.fixture()
def seller():
    return {
        "id": "SEL-9121-8944",
        "href": "/accounts/sellers/SEL-9121-8944",
        "name": "SWO US",
        "icon": "/static/SEL-9121-8944/icon.png",
        "address": {
            "country": "US",
            "region": "CA",
            "city": "San Jose",
            "addressLine1": "3601 Lyon St",
            "addressLine2": "",
            "postCode": "94123",
        },
        "contact": {
            "firstName": "Francesco",
            "lastName": "Faraone",
            "email": "francesco.faraone@softwareone.com",
            "phone": {
                "prefix": "+1",
                "number": "4082954078",
            },
        },
    }


@pytest.fixture()
def template():
    return {
        "id": "TPL-1234-1234-4321",
        "name": "Default Template",
    }


@pytest.fixture()
def agreement(buyer, licensee, listing):
    return {
        "id": "AGR-2119-4550-8674-5962",
        "href": "/commerce/agreements/AGR-2119-4550-8674-5962",
        "icon": None,
        "name": "Product Name 1",
        "audit": {
            "created": {
                "at": "2023-12-14T18:02:16.9359",
                "by": {"id": "USR-0000-0001"},
            },
            "updated": None,
        },
        "subscriptions": [
            {
                "id": "SUB-1000-2000-3000",
                "status": "Active",
                "lines": [
                    {
                        "id": "ALI-0010",
                        "item": {
                            "id": "ITM-1234-1234-1234-0010",
                            "name": "Item 0010",
                            "externalIds": {
                                "vendor": "external-id1",
                            },
                        },
                        "quantity": 10,
                    }
                ],
            },
            {
                "id": "SUB-1234-5678",
                "status": "Terminated",
                "lines": [
                    {
                        "id": "ALI-0011",
                        "item": {
                            "id": "ITM-1234-1234-1234-0011",
                            "name": "Item 0011",
                            "externalIds": {
                                "vendor": "external-id2",
                            },
                        },
                        "quantity": 4,
                    }
                ],
            },
        ],
        "listing": listing,
        "licensee": licensee,
        "buyer": buyer,
        "seller": {
            "id": "SEL-9121-8944",
            "href": "/accounts/sellers/SEL-9121-8944",
            "name": "Software LN",
            "icon": "/static/SEL-9121-8944/icon.png",
            "address": {
                "country": "US",
            },
        },
        "client": {
            "id": "ACC-9121-8944",
            "href": "/accounts/sellers/ACC-9121-8944",
            "name": "Software LN",
            "icon": "/static/ACC-9121-8944/icon.png",
        },
        "product": {
            "id": "PRD-1111-1111",
        },
    }


@pytest.fixture()
def mpt_error_factory():
    """
    Generate an error message returned by the Marketplace platform.
    """

    def _mpt_error(
        status,
        title,
        detail,
        trace_id="00-27cdbfa231ecb356ab32c11b22fd5f3c-721db10d009dfa2a-00",
        errors=None,
    ):
        error = {
            "status": status,
            "title": title,
            "detail": detail,
            "traceId": trace_id,
        }
        if errors:
            error["errors"] = errors

        return error

    return _mpt_error


@pytest.fixture()
def mpt_list_response():
    def _wrap_response(objects_list):
        return {
            "data": objects_list,
        }

    return _wrap_response


@pytest.fixture()
def mock_env_webhook_secret():
    return '{ "webhook_secret": "WEBHOOK_SECRET" }'


@pytest.fixture()
def mocked_next_step(mocker):
    return mocker.MagicMock()


@pytest.fixture()
def ffc_organization():
    return {
        "name": "Nimbus Nexus Inc.",
        "currency": "EUR",
        "billing_currency": "USD",
        "operations_external_id": "AGR-9876-5534-9172",
        "events": {
            "created": {
                "at": "2025-04-03T15:04:25.894Z",
                "by": {"id": "string", "type": "user", "name": "Barack Obama"},
            },
            "updated": {
                "at": "2025-04-03T15:04:25.894Z",
                "by": {"id": "string", "type": "user", "name": "Barack Obama"},
            },
            "deleted": {
                "at": "2025-04-03T15:04:25.894Z",
                "by": {"id": "string", "type": "user", "name": "Barack Obama"},
            },
        },
        "id": "FORG-1234-1234-1234",
        "linked_organization_id": "ee7ebfaf-a222-4209-aecc-67861694a488",
        "status": "active",
        "expenses_info": {
            "limit": "10,000.00",
            "expenses_last_month": "4,321.26",
            "expenses_this_month": "2,111.49",
            "expenses_this_month_forecast": "5,001.12",
            "possible_monthly_saving": "4.66",
        },
    }


@pytest.fixture()
def fetch_terminated_entitlement():
    return {
        "name": "Test with Antonio",
        "affiliate_external_id": "AGR-1234-5678-9012",
        "datasource_id": "e30e2a6e-0712-48c3-8685-3298df063633",
        "id": "FENT-9763-4488-4624",
        "linked_datasource_id": "89d63330-92d1-45dc-a408-5a768ae22f9f",
        "linked_datasource_name": "MPT (Dev)",
        "linked_datasource_type": "azure_cnr",
        "owner": {"id": "FACC-3887-7055", "name": "Microsoft CSP", "type": "affiliate"},
        "status": "terminated",
        "events": {
            "created": {
                "at": "2025-05-06T08:39:09.584186Z",
                "by": {"id": "FUSR-5352-1497", "type": "user", "name": "Francesco Faraone"},
            },
            "updated": {
                "at": "2025-05-12T07:47:17.877365Z",
                "by": {"id": "FTKN-4573-9711", "type": "system", "name": "Microsoft CSP Extension"},
            },
            "redeemed": {
                "at": "2025-05-06T08:39:45.995072Z",
                "by": {
                    "id": "FORG-1317-5652-8045",
                    "name": "SoftwareOne (Test Environment)",
                    "operations_external_id": "AGR-4480-3352-1794",
                },
            },
            "terminated": {
                "at": "2025-06-28T07:47:19.142190Z",
                "by": {"id": "FTKN-4573-9711", "type": "system", "name": "Microsoft CSP Extension"},
            },
        },
    }


@pytest.fixture()
def active_entitlement():
    return {
        "name": "Test with Antonio",
        "affiliate_external_id": "AGR-1234-5678-9012",
        "datasource_id": "e30e2a6e-0712-48c3-8685-3298df063633",
        "id": "FENT-9763-4488-4624",
        "linked_datasource_id": "89d63330-92d1-45dc-a408-5a768ae22f9f",
        "linked_datasource_name": "MPT (Dev)",
        "linked_datasource_type": "azure_cnr",
        "owner": {"id": "FACC-3887-7055", "name": "Microsoft CSP", "type": "affiliate"},
        "status": "active",
        "events": {
            "created": {
                "at": "2025-09-06T08:39:09.584186Z",
                "by": {"id": "FUSR-5352-1497", "type": "user", "name": "Peter Parker"},
            },
            "updated": {
                "at": "2025-09-12T07:47:17.877365Z",
                "by": {
                    "id": "FTKN-4573-9711",
                    "type": "system",
                    "name": "Microsoft CSP Extension",
                },
            },
            "redeemed": {
                "at": "2025-09-06T08:39:45.995072Z",
                "by": {
                    "id": "FORG-1317-5652-8045",
                    "name": "SoftwareOne (Test Environment)",
                    "operations_external_id": "AGR-4480-3352-1794",
                },
            },
        },
    }


@pytest.fixture()
def expenses():
    org_id = "FORG-4801-6958-2949"

    def _create_datasource_expenses(
        id,
        datasource_id,
        linked_datasource_id,
        datasource_name,
        linked_datasource_type,
        expenses,
        total_expenses,
        year=2025,
        month=5,
        day=31,
        created_at="2025-05-31T09:00:10.000000Z",
        updated_at="2025-05-31T21:00:10.900386Z",
    ):
        return DatasourceExpense(
            id=id,
            datasource_id=datasource_id,
            linked_datasource_id=linked_datasource_id,
            datasource_name=datasource_name,
            linked_datasource_type=DatasourceType(linked_datasource_type),
            organization_id=org_id,
            year=year,
            month=month,
            day=day,
            expenses=Decimal(expenses),
            total_expenses=Decimal(total_expenses),
            created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(updated_at.replace("Z", "+00:00")),
        )

    raw_expenses = [
        {
            "id": "FDSX-9720-0822-5699",
            "datasource_id": "2d2f328c-1407-4e5e-ba59-1cbad182940f",
            "linked_datasource_id": "947cbf94-afc3-4055-b96d-eff284c36a09",
            "datasource_name": "CHaaS (Production)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "5484.1464",
            "total_expenses": "5484.1464",
            "created_at": "2025-05-31T09:00:10.791181Z",
        },
        {
            "id": "FDSX-1412-2194-1623",
            "datasource_id": "6c73c89e-7e5b-43b5-a7c4-1b0cb260dafb",
            "linked_datasource_id": "1aa5f619-eab6-4d80-a11f-b2765c4a4795",
            "datasource_name": "CHaaS (QA)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "2244.3480",
            "total_expenses": "2244.3480",
            "created_at": "2025-05-31T09:00:10.895964Z",
        },
        {
            "id": "FDSX-7626-5167-0610",
            "datasource_id": "91819a1c-c7d3-4b89-bc9f-39f85bff4666",
            "linked_datasource_id": "d4321470-cfa8-4a67-adf5-c11faf491e14",
            "datasource_name": "CPA (Development and Test)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "36368.0435",
            "total_expenses": "36368.0435",
            "created_at": "2025-05-31T09:00:10.935998Z",
        },
        {
            "id": "FDSX-3900-5021-3406",
            "datasource_id": "01643997-4d64-4718-8114-15e488ce3f61",
            "linked_datasource_id": "100efd88-28fb-49f1-946b-edbf78ad4650",
            "datasource_name": "CPA (Infrastructure)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "12012.9029",
            "total_expenses": "12012.9029",
            "created_at": "2025-05-31T09:00:10.980464Z",
        },
        {
            "id": "FDSX-5514-3587-5985",
            "datasource_id": "b6689fdb-ac8c-4116-8136-c7a179cb5be6",
            "linked_datasource_id": "1812ae7a-890f-413a-a4e3-9a76c357cfb2",
            "datasource_name": "CPA (QA and Production)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "140492.1680",
            "total_expenses": "140492.1680",
            "created_at": "2025-05-31T09:00:11.020795Z",
        },
        {
            "id": "FDSX-9091-3723-8599",
            "datasource_id": "203689795269",
            "linked_datasource_id": "b9204d35-9508-423e-8c0e-493d7c89f123",
            "datasource_name": "Marketplace (Dev)",
            "linked_datasource_type": "aws_cnr",
            "expenses": "449.7770",
            "total_expenses": "449.7770",
            "created_at": "2025-05-31T09:00:11.061262Z",
        },
        {
            "id": "FDSX-3762-3669-2884",
            "datasource_id": "654035049067",
            "linked_datasource_id": "3f584d10-4293-4599-8ad5-413acc72fd45",
            "datasource_name": "Marketplace (Production)",
            "linked_datasource_type": "aws_cnr",
            "expenses": "763.9655",
            "total_expenses": "763.9655",
            "created_at": "2025-05-31T09:00:11.104151Z",
        },
        {
            "id": "FDSX-4432-7370-5890",
            "datasource_id": "563690021965",
            "linked_datasource_id": "fb0088de-2e3c-4ffe-b6e4-dc075503473d",
            "datasource_name": "Marketplace (Staging)",
            "linked_datasource_type": "aws_cnr",
            "expenses": "1.5603",
            "total_expenses": "1.5603",
            "created_at": "2025-05-31T09:00:11.142825Z",
        },
        {
            "id": "FDSX-5882-3175-6293",
            "datasource_id": "89b098bc-b400-4578-8058-8416b0c25f6b",
            "linked_datasource_id": "cb78a18a-6adc-4780-9402-d175086accdc",
            "datasource_name": "MPT Finops (Production)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "2866.7103",
            "total_expenses": "2866.7103",
            "created_at": "2025-05-31T09:00:11.402325Z",
        },
        {
            "id": "FDSX-5883-8914-3036",
            "datasource_id": "63f2c438-c0e1-4606-ac10-eb6aa149c6cb",
            "linked_datasource_id": "12fa3bce-5513-40c8-96d7-0be2fc47ebcf",
            "datasource_name": "MPT Finops (Staging)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "2948.0483",
            "total_expenses": "2948.0483",
            "created_at": "2025-05-31T09:00:11.602225Z",
        },
        {
            "id": "FDSX-5383-4251-5606",
            "datasource_id": "285102913731",
            "linked_datasource_id": "c86dfcec-08ba-4007-a617-8f53efbfba06",
            "datasource_name": "SoftwareOne AWS",
            "linked_datasource_type": "aws_cnr",
            "expenses": "147974.7328",
            "total_expenses": "147974.7328",
            "created_at": "2025-05-31T09:00:11.729544Z",
        },
        {
            "id": "FDSX-9914-5293-7158",
            "datasource_id": "996403779197",
            "linked_datasource_id": "2a3db41b-bcd9-48b1-824f-87acfb510f88",
            "datasource_name": "Marketplace (Test)",
            "linked_datasource_type": "aws_cnr",
            "expenses": "22.3045",
            "total_expenses": "22.3045",
            "created_at": "2025-05-31T09:00:11.185263Z",
        },
        {
            "id": "FDSX-8478-3286-4449",
            "datasource_id": "e30e2a6e-0712-48c3-8685-3298df063633",
            "linked_datasource_id": "b509e2e2-20a4-48eb-ac60-b291338feff4",
            "datasource_name": "MPT (Dev)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "3678.8134",
            "total_expenses": "3678.8134",
            "created_at": "2025-05-31T09:00:11.224685Z",
        },
        {
            "id": "FDSX-5166-9927-9966",
            "datasource_id": "ef415e11-361a-4f91-8b3c-23aeb9c8f2ac",
            "linked_datasource_id": "96e23b8d-854b-42d7-8b59-264e6f314b2d",
            "datasource_name": "MPT (Production)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "0.0004",
            "total_expenses": "0.0004",
            "created_at": "2025-05-31T09:00:11.264197Z",
        },
        {
            "id": "FDSX-3043-7639-0675",
            "datasource_id": "dea8e892-1212-42c9-afa0-3b87e7bfffd5",
            "linked_datasource_id": "a611abd8-9cde-4b17-ab54-31f9d43dc955",
            "datasource_name": "MPT (Test)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "2564.4489",
            "total_expenses": "2564.4489",
            "created_at": "2025-05-31T09:00:11.312828Z",
        },
        {
            "id": "FDSX-6912-0266-0891",
            "datasource_id": "a7e5cb3a-1b68-445b-9234-7cebea7a6458",
            "linked_datasource_id": "fe5d1e82-2b10-4786-8f44-0dfd7ac3144a",
            "datasource_name": "MPT Platform (Staging)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "0.0000",
            "total_expenses": "0.0000",
            "created_at": "2025-05-31T09:00:11.688224Z",
            "updated_at": "2025-05-31T09:00:11.688232Z",
        },
        {
            "id": "FDSX-3079-0267-3379",
            "datasource_id": "a37be38a-56e4-4fab-8e3c-e4738f50ad70",
            "linked_datasource_id": "29b2698f-6110-4a7c-88f7-58a14e4db6af",
            "datasource_name": "MPT Finops (Test)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "0.0000",
            "total_expenses": "0.0000",
            "created_at": "2025-05-31T09:00:11.644465Z",
            "updated_at": "2025-05-31T09:00:11.644473Z",
        },
        {
            "id": "FDSX-3452-5162-7796",
            "datasource_id": "6964b7a4-9ce4-4975-98d7-b9a2e3b0a48e",
            "linked_datasource_id": "0708f18c-b23a-4652-8fd1-5d95f89226a9",
            "datasource_name": "MPT Finops (Dev)",
            "linked_datasource_type": "azure_cnr",
            "expenses": "0.0000",
            "total_expenses": "0.0000",
            "created_at": "2025-05-31T09:00:11.356732Z",
            "updated_at": "2025-05-31T09:00:11.356739Z",
        },
    ]

    return [_create_datasource_expenses(**item) for item in raw_expenses]


@pytest.fixture()
def daily_expenses():
    return {
        1: Decimal("1957.9254"),
        2: Decimal("3233.8422"),
        3: Decimal("3170.0376"),
        4: Decimal("4982.3398"),
        5: Decimal("3746.7108"),
        6: Decimal("2503.8501"),
        7: Decimal("2518.9622"),
        8: Decimal("1186.67"),
        9: Decimal("4132.4113"),
        10: Decimal("1544.0553"),
        11: Decimal("2981.121"),
        12: Decimal("1289.2675"),
        13: Decimal("2770.6942"),
        14: Decimal("1133.5218"),
        15: Decimal("1133.1845"),
        16: Decimal("4716.4833"),
        17: Decimal("3406.0789"),
        18: Decimal("2654.5862"),
        19: Decimal("3317.5269"),
        20: Decimal("4820.0637"),
        21: Decimal("3542.4266"),
        22: Decimal("3280.8039"),
        23: Decimal("4401.6766"),
        24: Decimal("4175.2924"),
        25: Decimal("2377.7552"),
        26: Decimal("4432.751"),
        27: Decimal("4777.9023"),
        28: Decimal("5126.0458"),
        29: Decimal("5226.0458"),
        30: Decimal("5326.0458"),
    }


@pytest.fixture()
def ffc_employee():
    return {
        "email": "test@example.com",
        "display_name": "Tor James Parker",
        "created_at": "2025-04-04T09:11:36.291Z",
        "last_login": "2025-04-04T09:11:36.291Z",
        "roles_count": 0,
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    }


@pytest.fixture()
def billing_process_instance(request):
    params = {
        "month": 6,
        "year": 2025,
        "authorization": {
            "id": "AUT-5305-9928",
            "name": "TEST",
            "currency": "USD",
        },
    }

    # Override defaults if test provides parameters via @pytest.mark.parametrize indirect
    if param := getattr(request, "param", None):
        params.update(param)

    return AuthorizationProcessor(**params)


@pytest.fixture()
def authorization_process_result():
    return ProcessResultInfo(
        authorization_id="AUT-5305-9928",
    )


@pytest.fixture()
def create_journal_response():
    return {
        "$meta": {
            "omitted": ["processing"],
        },
        "id": "BJO-9000-4019",
        "name": "June 2025 Charges",
        "externalIds": {
            "vendor": "202506",
        },
        "status": "Draft",
        "vendor": {
            "id": "ACC-3102-8586",
            "type": "Vendor",
            "status": "Active",
            "name": "FinOps for Cloud",
            "icon": "/v1/accounts/accounts/ACC-3102-8586/icon",
        },
        "owner": {
            "id": "SEL-7032-1456",
            "externalId": "US",
            "name": "SoftwareONE Inc.",
            "icon": "/v1/accounts/sellers/SEL-7032-1456/icon",
        },
        "product": {
            "id": "PRD-2426-7318",
            "name": "FinOps for Cloud",
            "externalIds": {
                "operations": "adsasadsa",
            },
            "icon": "/v1/catalog/products/PRD-2426-7318/icon",
            "status": "Published",
        },
        "authorization": {
            "id": "AUT-5305-9928",
            "name": "asdasdsa",
            "currency": "USD",
        },
        "dueDate": "2025-07-01T00:00:00.000Z",
        "price": {
            "currency": "USD",
            "totalPP": 0.00000,
        },
        "upload": {
            "total": 0,
            "split": 0,
            "ready": 0,
            "error": 0,
        },
        "audit": {
            "created": {
                "at": "2025-06-10T17:04:53.802Z",
                "by": {
                    "id": "TKN-5645-5497",
                    "name": "Antonio Di Mariano",
                    "icon": "",
                },
            },
            "updated": {},
        },
    }


@pytest.fixture()
def existing_journal_file_response():
    return {
        "$meta": {
            "pagination": {"offset": 0, "limit": 10, "total": 1},
            "omitted": ["processing", "audit"],
        },
        "data": [
            {
                "id": "BJO-9000-4019",
                "name": "June 2025 Charges",
                "externalIds": {
                    "vendor": "202506",
                },
                "status": "Draft",
                "vendor": {
                    "id": "ACC-3102-8586",
                    "type": "Vendor",
                    "status": "Active",
                    "name": "FinOps for Cloud",
                    "icon": "/v1/accounts/accounts/ACC-3102-8586/icon",
                },
                "owner": {
                    "id": "SEL-7032-1456",
                    "externalId": "US",
                    "name": "SoftwareONE Inc.",
                    "icon": "/v1/accounts/sellers/SEL-7032-1456/icon",
                },
                "product": {
                    "id": "PRD-2426-7318",
                    "name": "FinOps for Cloud",
                    "externalIds": {
                        "operations": "adsasadsa",
                    },
                    "icon": "/v1/catalog/products/PRD-2426-7318/icon",
                    "status": "Published",
                },
                "authorization": {
                    "id": "AUT-5305-9928",
                    "name": "asdasdsa",
                    "currency": "USD",
                },
                "dueDate": "2025-07-01T00:00:00.000Z",
                "price": {
                    "currency": "USD",
                    "totalPP": 0.00000,
                },
                "upload": {
                    "total": 0,
                    "split": 0,
                    "ready": 0,
                    "error": 0,
                },
            },
        ],
    }


@pytest.fixture()
def journal_attachment_response():
    return {
        "$meta": {
            "pagination": {"offset": 0, "limit": 10, "total": 1},
            "omitted": ["processing", "audit"],
        },
        "data": [
            {
                "id": "JOA-5985-1983",
                "name": "charge_file.json",
                "journal": {
                    "id": "BJO-9000-4019",
                    "name": "June 2025 Charges",
                    "dueDate": "2025-07-01T00:00:00.000Z",
                },
                "vendor": {
                    "id": "ACC-3102-8586",
                    "type": "Vendor",
                    "status": "Active",
                    "name": "FinOps for Cloud",
                    "icon": "/v1/accounts/accounts/ACC-3102-8586/icon",
                },
                "type": "Attachment",
                "filename": "charge_file.json",
                "size": 2981,
                "contentType": "application/json",
                "description": "Conversion Rate",
                "isDeleted": False,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Shared agreement data builders
# ---------------------------------------------------------------------------

_AGREEMENT_ORDERING_PARAMS = [
    {
        "id": "PAR-7208-0459-0004",
        "externalId": "organizationName",
        "name": "Organization Name",
        "type": "SingleLineText",
        "phase": "Order",
        "displayValue": "Software One",
        "value": "Software One",
    },
    {
        "id": "PAR-7208-0459-0005",
        "externalId": "adminContact",
        "name": "Administrator",
        "type": "Contact",
        "phase": "Order",
        "displayValue": "JJ Adams jj@softwareone123.com",
        "value": {
            "firstName": "JJ",
            "lastName": "Adams",
            "email": "jj@softwareone123.com",
            "phone": None,
        },
    },
    {
        "id": "PAR-7208-0459-0006",
        "externalId": "currency",
        "name": "Currency",
        "type": "DropDown",
        "phase": "Order",
        "displayValue": "EUR",
        "value": "EUR",
    },
]

_AGREEMENT_BASE_FULFILLMENT_PARAMS = [
    {
        "id": "PAR-7208-0459-0007",
        "externalId": "dueDate",
        "name": "Due date",
        "type": "Date",
        "phase": "Fulfillment",
    },
    {
        "id": "PAR-7208-0459-0008",
        "externalId": "isNewUser",
        "name": "Is new user?",
        "type": "Checkbox",
        "phase": "Fulfillment",
    },
    {
        "id": "PAR-7208-0459-0011",
        "externalId": "billedPercentage",
        "name": "Billed percentage of monthly spend",
        "type": "SingleLineText",
        "phase": "Fulfillment",
        "displayValue": "4",
        "value": "4",
    },
]

_AGREEMENT_TRIAL_FULFILLMENT_PARAMS = [
    {
        "id": "PAR-7208-0459-0009",
        "externalId": "trialStartDate",
        "name": "Trial period start date",
        "type": "Date",
        "phase": "Fulfillment",
        "displayValue": "2025-06-01",
        "value": "2025-06-01",
    },
    {
        "id": "PAR-7208-0459-0010",
        "externalId": "trialEndDate",
        "name": "Trial period end date",
        "type": "Date",
        "phase": "Fulfillment",
        "displayValue": "2025-06-15",
        "value": "2025-06-15",
    },
]


def _build_agreement_data(include_trial: bool = True, **overrides) -> list[dict]:
    """
    Build a single-element agreement list used by billing test fixtures.

    Parameters:
        include_trial: when True the default fulfillment parameters include
            trialStartDate / trialEndDate entries (2025-06-01 → 2025-06-15).
        **overrides: keyword arguments are shallow-merged into the agreement
            dict via ``dict.update``, allowing callers to replace any top-level
            key (e.g. ``parameters``) without touching the rest of the data.
    """
    # Keep base params order: dueDate, isNewUser, [trial params,] billedPercentage
    fulfillment = (
        _AGREEMENT_BASE_FULFILLMENT_PARAMS[:2]
        + (_AGREEMENT_TRIAL_FULFILLMENT_PARAMS if include_trial else [])
        + _AGREEMENT_BASE_FULFILLMENT_PARAMS[2:]
    )

    data = [
        {
            "id": "AGR-4528-5004-9617",
            "status": "Active",
            "listing": {"id": "LST-9168-7963"},
            "authorization": {
                "id": "AUT-5305-9928",
                "name": "SoftwareOne FinOps for Cloud (USD)",
                "currency": "USD",
            },
            "vendor": {
                "id": "ACC-3805-2089",
                "type": "Vendor",
                "status": "Active",
                "name": "SoftwareOne Vendor",
                "icon": "/v1/accounts/accounts/ACC-3805-2089/icon",
            },
            "client": {
                "id": "ACC-5563-4382",
                "type": "Client",
                "status": "Active",
                "name": "Adastraflex 2.0",
                "icon": "/v1/accounts/accounts/ACC-5563-4382/icon",
            },
            "price": {"PPxY": 0.00000, "PPxM": 0.00000, "currency": "USD"},
            "template": {"id": "TPL-7208-0459-0006", "name": "Purchase"},
            "name": "SoftwareOne FinOps for Cloud for Adastraflex 2.0",
            "parameters": {
                "ordering": list(_AGREEMENT_ORDERING_PARAMS),
                "fulfillment": fulfillment,
            },
            "licensee": {"id": "LCE-1815-3571-9260", "name": "Pawels Licensee US"},
            "buyer": {"id": "BUY-6923-7488", "name": "Pawels Buyer"},
            "seller": {
                "id": "SEL-7282-9889",
                "externalId": "78ADB9DA-BC69-4CBF-BAA0-CDBC28619EF7",
                "name": "SoftwareOne, Inc.",
                "icon": "/v1/accounts/sellers/SEL-7282-9889/icon",
            },
            "product": {
                "id": "PRD-7208-0459",
                "name": "SoftwareOne FinOps for Cloud",
                "externalIds": {},
                "icon": "/v1/catalog/products/PRD-7208-0459/icon",
                "status": "Published",
            },
            "externalIds": {"client": "", "vendor": "FORG-1919-6513-6770"},
        }
    ]
    if overrides:
        data[0].update(overrides)
    return data


@pytest.fixture()
def agreement_data_with_trial():
    def _factory(**overrides):
        return _build_agreement_data(include_trial=True, **overrides)

    return _factory


@pytest.fixture()
def agreement_data_no_trial():
    def _factory(**overrides):
        return _build_agreement_data(include_trial=False, **overrides)

    return _factory


@pytest.fixture()
def agreement_fulfillment():
    return [
        {
            "externalId": "dueDate",
            "id": "PAR-7208-0459-0007",
            "name": "Due date",
            "phase": "Fulfillment",
            "type": "Date",
        },
        {
            "externalId": "isNewUser",
            "id": "PAR-7208-0459-0008",
            "name": "Is new user?",
            "phase": "Fulfillment",
            "type": "Checkbox",
        },
        {
            "displayValue": "2025-06-01",
            "externalId": "trialStartDate",
            "id": "PAR-7208-0459-0009",
            "name": "Trial period start date",
            "phase": "Fulfillment",
            "type": "Date",
            "value": "2025-06-01",
        },
        {
            "displayValue": "2025-06-15",
            "externalId": "trialEndDate",
            "id": "PAR-7208-0459-0010",
            "name": "Trial period end date",
            "phase": "Fulfillment",
            "type": "Date",
            "value": "2025-06-15",
        },
        {
            "displayValue": "4",
            "externalId": "billedPercentage",
            "id": "PAR-7208-0459-0011",
            "name": "Billed percentage of monthly spend",
            "phase": "Fulfillment",
            "type": "SingleLineText",
            "value": "4",
        },
    ]


@pytest.fixture()
def organization_data():
    return {
        "name": "SoftwareOne (Test Environment)",
        "currency": "USD",
        "billing_currency": "EUR",
        "operations_external_id": "ACC-1234-5678",
        "events": {
            "created": {
                "at": "2025-04-03T15:18:02.408803Z",
                "by": {
                    "id": "FUSR-6956-9254",
                    "type": "user",
                    "name": "FrancescoFaraone",
                },
            },
            "updated": {
                "at": "2025-04-22T13:32:00.599322Z",
                "by": {
                    "id": "FUSR-6956-9254",
                    "type": "user",
                    "name": "FrancescoFaraone",
                },
            },
        },
        "id": "FORG-4801-6958-2949",
        "linked_organization_id": "3d0fe384-b1cf-4929-ad5e-1aa544f93dd5",
        "status": "active",
    }


@pytest.fixture()
def catalog_authorizations():
    return {
        "$meta": {"pagination": {"offset": 0, "limit": 10, "total": 1}, "omitted": ["audit"]},
        "data": [
            {
                "id": "AUT-5305-9928",
                "name": "asdasdsa",
                "externalIds": {},
                "currency": "USD",
                "notes": "",
                "product": {
                    "id": "PRD-2426-7318",
                    "name": "FinOps for Cloud",
                    "externalIds": {"operations": "adsasadsa"},
                    "icon": "/v1/catalog/products/PRD-2426-7318/icon",
                    "status": "Published",
                },
                "vendor": {
                    "id": "ACC-3102-8586",
                    "type": "Vendor",
                    "status": "Active",
                    "name": "FinOps for Cloud",
                    "icon": "/v1/accounts/accounts/ACC-3102-8586/icon",
                },
                "owner": {
                    "id": "SEL-7032-1456",
                    "externalId": "US",
                    "name": "SoftwareONE Inc.",
                    "icon": "/v1/accounts/sellers/SEL-7032-1456/icon",
                },
                "statistics": {"subscriptions": 7, "agreements": 12, "sellers": 2, "listings": 2},
                "journal": {"firstInvoiceDate": "2025-02-01T00:00:00.000Z", "frequency": "1m"},
                "eligibility": {"client": True, "partner": False},
            }
        ],
    }


@pytest.fixture()
def catalog_authorization():
    return {
        "id": "AUT-5305-9928",
        "name": "asdasdsa",
        "externalIds": {},
        "currency": "USD",
        "notes": "",
        "product": {
            "id": "PRD-2426-7318",
            "name": "FinOps for Cloud",
            "externalIds": {"operations": "adsasadsa"},
            "icon": "/v1/catalog/products/PRD-2426-7318/icon",
            "status": "Published",
        },
        "vendor": {
            "id": "ACC-3102-8586",
            "type": "Vendor",
            "status": "Active",
            "name": "FinOps for Cloud",
            "icon": "/v1/accounts/accounts/ACC-3102-8586/icon",
        },
        "owner": {
            "id": "SEL-7032-1456",
            "externalId": "US",
            "name": "SoftwareONE Inc.",
            "icon": "/v1/accounts/sellers/SEL-7032-1456/icon",
        },
        "statistics": {"subscriptions": 7, "agreements": 12, "sellers": 2, "listings": 2},
        "journal": {"firstInvoiceDate": "2025-02-01T00:00:00.000Z", "frequency": "1m"},
        "eligibility": {"client": True, "partner": False},
        "audit": {
            "created": {
                "at": "2024-10-23T15:39:19.138Z",
                "by": {"id": "USR-6476-8245", "name": "Francesco Faraone"},
            }
        },
    }


@pytest.fixture()
def agreements():
    return {
        "$meta": {
            "pagination": {"offset": 0, "limit": 1000, "total": 1},
            "omitted": [
                "lines",
                "assets",
                "subscriptions",
                "split",
                "termsAndConditions",
                "certificates",
            ],
        },
        "data": [
            {
                "id": "AGR-4985-4034-6503",
                "status": "Active",
                "listing": {
                    "id": "LST-9168-7963",
                },
                "authorization": {
                    "id": "AUT-5305-9928",
                    "name": "SoftwareOne FinOps for Cloud (USD)",
                    "currency": "USD",
                },
                "vendor": {
                    "id": "ACC-3805-2089",
                    "type": "Vendor",
                    "status": "Active",
                    "name": "SoftwareOne Vendor",
                    "icon": "/v1/accounts/accounts/ACC-3805-2089/icon",
                },
                "client": {
                    "id": "ACC-5809-3083",
                    "type": "Client",
                    "status": "Active",
                    "name": "Area302 (Client)",
                    "icon": "/v1/accounts/accounts/ACC-5809-3083/icon",
                },
                "price": {
                    "PPxY": 0.00000,
                    "PPxM": 0.00000,
                    "currency": "USD",
                },
                "template": {
                    "id": "TPL-7208-0459-0003",
                    "name": "Default",
                },
                "name": "SoftwareOne FinOps for Cloud for Area302 (Client)",
                "parameters": {
                    "ordering": [
                        {
                            "id": "PAR-7208-0459-0004",
                            "externalId": "organizationName",
                            "name": "Organization Name",
                            "type": "SingleLineText",
                            "phase": "Order",
                            "displayValue": "PL Organization",
                            "value": "PL Organization",
                        },
                        {
                            "id": "PAR-7208-0459-0005",
                            "externalId": "adminContact",
                            "name": "Administrator",
                            "type": "Contact",
                            "phase": "Order",
                            "displayValue": "PL NNN pavel.lonkin@softwareone.com",
                            "value": {
                                "firstName": "PL",
                                "lastName": "NNN",
                                "email": "pavel.lonkin@softwareone.com",
                                "phone": None,
                            },
                        },
                        {
                            "id": "PAR-7208-0459-0006",
                            "externalId": "currency",
                            "name": "Currency",
                            "type": "DropDown",
                            "phase": "Order",
                            "displayValue": "EUR",
                            "value": "EUR",
                        },
                    ],
                    "fulfillment": [
                        {
                            "id": "PAR-7208-0459-0007",
                            "externalId": "dueDate",
                            "name": "Due Date",
                            "type": "Date",
                            "phase": "Fulfillment",
                        },
                    ],
                },
                "licensee": {
                    "id": "LCE-3603-9310-4566",
                    "name": "Adobe Licensee 302",
                },
                "buyer": {
                    "id": "BUY-0280-5606",
                    "name": "Rolls-Royce Corporation",
                    "icon": "/v1/accounts/buyers/BUY-0280-5606/icon",
                },
                "seller": {
                    "id": "SEL-7282-9889",
                    "externalId": "78ADB9DA-BC69-4CBF-BAA0-CDBC28619EF7",
                    "name": "SoftwareOne, Inc.",
                    "icon": "/v1/accounts/sellers/SEL-7282-9889/icon",
                },
                "product": {
                    "id": "PRD-7208-0459",
                    "name": "SoftwareOne FinOps for Cloud",
                    "externalIds": {},
                    "icon": "/v1/catalog/products/PRD-7208-0459/icon",
                    "status": "Published",
                },
                "externalIds": {
                    "client": "",
                    "vendor": "FORG-6649-3383-1832",
                },
            }
        ],
    }


@pytest.fixture()
def currency_conversion(exchange_rates):
    return {
        "base_currency": "USD",
        "billing_currency": "EUR",
        "exchange_rate": Decimal("0.8636"),
        "exchange_rates": exchange_rates,
    }


@pytest.fixture()
def exchange_rates():
    return {
        "result": "success",
        "documentation": "https://www.exchangerate-api.com/docs",
        "terms_of_use": "https://www.exchangerate-api.com/terms",
        "time_last_update_unix": 1749772801,
        "time_last_update_utc": "Fri, 13 Jun 2025 00:00:01 +0000",
        "time_next_update_unix": 1749859201,
        "time_next_update_utc": "Sat, 14 Jun 2025 00:00:01 +0000",
        "base_code": "USD",
        "conversion_rates": {
            "USD": 1,
            "AED": 3.6725,
            "AFN": 69.5472,
            "ALL": 85.1093,
            "AMD": 383.3873,
            "ANG": 1.7900,
            "AOA": 918.3743,
            "ARS": 1185.5000,
            "AUD": 1.5327,
            "AWG": 1.7900,
            "AZN": 1.6992,
            "BAM": 1.6892,
            "BBD": 2.0000,
            "BDT": 122.1719,
            "BGN": 1.6890,
            "BHD": 0.3760,
            "BIF": 2971.7492,
            "BMD": 1.0000,
            "BND": 1.2792,
            "BOB": 6.9152,
            "BRL": 5.5370,
            "BSD": 1.0000,
            "BTN": 85.5923,
            "BWP": 13.3716,
            "BYN": 3.2669,
            "BZD": 2.0000,
            "CAD": 1.3609,
            "CDF": 2886.4367,
            "CHF": 0.8117,
            "CLP": 933.6466,
            "CNY": 7.1775,
            "COP": 4186.1683,
            "CRC": 506.5810,
            "CUP": 24.0000,
            "CVE": 95.2338,
            "CZK": 21.3879,
            "DJF": 177.7210,
            "DKK": 6.4402,
            "DOP": 59.0220,
            "DZD": 130.8973,
            "EGP": 49.7557,
            "ERN": 15.0000,
            "ETB": 134.8766,
            "EUR": 0.8636,
            "FJD": 2.2443,
            "FKP": 0.7353,
            "FOK": 6.4410,
            "GBP": 0.7353,
            "GEL": 2.7292,
            "GGP": 0.7353,
            "GHS": 10.8065,
            "GIP": 0.7353,
            "GMD": 72.7261,
            "GNF": 8687.5475,
            "GTQ": 7.6750,
            "GYD": 209.2835,
            "HKD": 7.8497,
            "HNL": 26.0450,
            "HRK": 6.5074,
            "HTG": 130.9916,
            "HUF": 346.2904,
            "IDR": 16225.9113,
            "ILS": 3.5607,
            "IMP": 0.7353,
            "INR": 85.5933,
            "IQD": 1307.6716,
            "IRR": 41954.7543,
            "ISK": 124.3409,
            "JEP": 0.7353,
            "JMD": 159.2592,
            "JOD": 0.7090,
            "JPY": 143.5195,
            "KES": 129.0672,
            "KGS": 87.3928,
            "KHR": 4017.1102,
            "KID": 1.5329,
            "KMF": 424.9034,
            "KRW": 1354.9252,
            "KWD": 0.3058,
            "KYD": 0.8333,
            "KZT": 511.6331,
            "LAK": 21653.3424,
            "LBP": 89500.0000,
            "LKR": 298.6639,
            "LRD": 199.5512,
            "LSL": 17.7775,
            "LYD": 5.4592,
            "MAD": 9.0986,
            "MDL": 17.2013,
            "MGA": 4499.8917,
            "MKD": 53.8655,
            "MMK": 2095.7236,
            "MNT": 3569.2457,
            "MOP": 8.0852,
            "MRU": 39.6769,
            "MUR": 45.4594,
            "MVR": 15.4172,
            "MWK": 1738.8487,
            "MXN": 18.9026,
            "MYR": 4.2226,
            "MZN": 63.8810,
            "NAD": 17.7775,
            "NGN": 1536.0716,
            "NIO": 36.7269,
            "NOK": 9.9437,
            "NPR": 136.9476,
            "NZD": 1.6495,
            "OMR": 0.3845,
            "PAB": 1.0000,
            "PEN": 3.6211,
            "PGK": 4.1514,
            "PHP": 55.7289,
            "PKR": 282.2843,
            "PLN": 3.6835,
            "PYG": 8001.9463,
            "QAR": 3.6400,
            "RON": 4.3450,
            "RSD": 101.2894,
            "RUB": 79.8143,
            "RWF": 1436.0247,
            "SAR": 3.7500,
            "SBD": 8.5594,
            "SCR": 14.8355,
            "SDG": 510.8585,
            "SEK": 9.4431,
            "SGD": 1.2792,
            "SHP": 0.7353,
            "SLE": 22.3674,
            "SLL": 22367.3971,
            "SOS": 570.7579,
            "SRD": 37.3233,
            "SSP": 4634.0855,
            "STN": 21.1602,
            "SYP": 12892.7896,
            "SZL": 17.7775,
            "THB": 32.4006,
            "TJS": 10.0570,
            "TMT": 3.4978,
            "TND": 2.9285,
            "TOP": 2.3506,
            "TRY": 39.3856,
            "TTD": 6.7715,
            "TVD": 1.5329,
            "TWD": 29.3672,
            "TZS": 2582.2337,
            "UAH": 41.5300,
            "UGX": 3594.8408,
            "UYU": 41.2386,
            "UZS": 12703.3397,
            "VES": 101.0822,
            "VND": 26033.7896,
            "VUV": 119.0876,
            "WST": 2.7383,
            "XAF": 566.5378,
            "XCD": 2.7000,
            "XCG": 1.7900,
            "XDR": 0.7278,
            "XOF": 566.5378,
            "XPF": 103.0648,
            "YER": 243.0015,
            "ZAR": 17.7777,
            "ZMW": 24.8208,
            "ZWL": 6.9749,
        },
    }


@pytest.fixture()
def org_mock_generator(get_organizations):
    async def _gen():
        yield get_organizations

    return _gen


@pytest.fixture()
def org_mock_generator_agr_000(get_organizations):
    get_organizations.operations_external_id = "AGR-0000-0000-0000"

    async def _gen():
        yield get_organizations

    return _gen


@pytest.fixture()
def agr_mock_generator(agreements):
    async def _gen():
        for agr in agreements["data"]:
            yield agr

    return _gen


@pytest.fixture()
def agr_mock_generator_with_trial(agreement_data_with_trial):
    async def _gen():
        for agr in agreement_data_with_trial():
            yield agr

    return _gen


@pytest.fixture()
def exp_mock_generator(expenses):
    async def _gen():
        for exp in expenses:
            yield exp

    return _gen


@pytest.fixture()
def patch_get_by_billing_currency(mocker, org_mock_generator):

    def _factory(*_args, **_kwargs):
        return org_mock_generator()

    return mocker.patch(
        "app.billing.process_billing.OrganizationHandler.get_by_billing_currency",
        side_effect=_factory,
    )


@pytest.fixture()
def patch_get_for_billing(mocker, active_entitlement):
    def _factory(*_args, **_kwargs):
        events = active_entitlement.get("events", {})
        redeemed_at = events.get("redeemed", {}).get("at")
        terminated_at = events.get("terminated", {}).get("at")
        return SimpleNamespace(
            id=active_entitlement.get("id"),
            redeemed_at=(
                datetime.fromisoformat(redeemed_at.replace("Z", "+00:00")) if redeemed_at else None
            ),
            terminated_at=(
                datetime.fromisoformat(terminated_at.replace("Z", "+00:00"))
                if terminated_at
                else None
            ),
        )

    return mocker.patch(
        "app.billing.process_billing.EntitlementHandler.get_for_billing",
        side_effect=_factory,
    )


@pytest.fixture()
def patch_get_agreements_from_mpt(mocker, billing_process_instance, agr_mock_generator):
    return mocker.patch.object(
        billing_process_instance.mpt_client,
        "get_agreements_by_organization",
        return_value=agr_mock_generator(),
    )


@pytest.fixture()
def patch_return_datasource_expenses(mocker, billing_process_instance, exp_mock_generator):
    return mocker.patch(
        "app.billing.process_billing.DatasourceExpenseHandler.get_expenses_for_billing",
        return_value=exp_mock_generator(),
    )


@pytest.fixture()
def patch_get_agreements_with_trial(
    mocker, billing_process_instance, agr_mock_generator_with_trial
):
    return mocker.patch.object(
        billing_process_instance.mpt_client,
        "get_agreements_by_organization",
        return_value=agr_mock_generator_with_trial(),
    )


@pytest.fixture()
def patch_get_by_billing_currency_for_agr_000(
    mocker, billing_process_instance, agr_mock_generator, org_mock_generator_agr_000
):
    return mocker.patch(
        "app.billing.process_billing.OrganizationHandler.get_by_billing_currency",
        return_value=org_mock_generator_agr_000(),
    )


class TestClientAuth(httpx.Auth):
    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = "Bearer fake token"
        yield request


class FakeAPIClient(BaseAPIClient):
    @property
    def base_url(self) -> str:
        return "https://local.local/v1"

    @property
    def auth(self):
        return TestClientAuth()

    def get_pagination_meta(self, response):
        return response["meta"]["pagination"]

    def get_page_data(self, response):
        return response["data"]


@pytest.fixture()
def fake_apiclient(test_settings: Settings):
    return FakeAPIClient(settings=test_settings)


@pytest.fixture()
def process_result_success_payload():
    return [
        ProcessResultInfo(
            authorization_id="AUTH-1234-5678",
            journal_id="BJO-1234-5678",
            result=ProcessResult.JOURNAL_GENERATED,
            message=None,
        ),
    ]


@pytest.fixture()
def process_result_with_warning():
    return [
        ProcessResultInfo(
            authorization_id="AUTH-1234-5678",
            journal_id="BJO-1234-5678",
            result=ProcessResult.JOURNAL_SKIPPED,
            message="Found the journal BJO-8604-8083 with status Review",
        ),
    ]


@pytest.fixture()
def process_result_with_error():
    return [
        ProcessResultInfo(
            authorization_id="AUTH-1234-5678",
            journal_id="BJO-1234-5678",
            result=ProcessResult.ERROR,
            message="Error",
        ),
    ]


@pytest.fixture()
def temp_charges_file():
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        yield f.name

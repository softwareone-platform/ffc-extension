import enum
import pathlib
from urllib.parse import quote

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = pathlib.Path(__file__).parent.parent


class OpenTelemetryExporter(str, enum.Enum):
    JAEGER = "jaeger"
    AZURE_APP_INSIGHTS = "azure_app_insights"
    CONSOLE = "console"


class Settings(BaseSettings):
    """
    Project settings loaded from environment variables
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="ffc_operations_",
        extra="ignore",
    )

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432

    api_modifier_base_url: str
    api_modifier_jwt_secret: str
    secrets_encryption_key: str
    auth_access_jwt_secret: str
    auth_access_jwt_lifespan_minutes: int = 5
    auth_refresh_jwt_secret: str
    auth_refresh_jwt_lifespan_days: int = 7
    invitation_token_length: int = 64
    invitation_token_expires_days: int = 7
    pwd_reset_token_length: int = 64
    pwd_reset_token_length_expires_minutes: int = 15

    system_jwt_token_max_lifespan_minutes: int = 5
    datasources_expenses_obsolete_after_months: int = 6
    billing_percentage: float = 1.0
    ffc_external_product_id: str = "FIN-0001-P1M"

    optscale_auth_api_base_url: str
    optscale_rest_api_base_url: str
    optscale_cluster_secret: str
    optscale_read_timeout: int = 90

    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_sender_email: str
    smtp_sender_name: str

    mpt_api_base_url: str
    mpt_extension_id: str
    mpt_extension_token: str
    mpt_api_rows_per_page: int = 100

    api_base_url: str = "https://api.finops.softwareone.com/ops/v1"
    cli_rich_logging: bool = True
    debug: bool = False

    opentelemetry_exporter: OpenTelemetryExporter | None = OpenTelemetryExporter.JAEGER
    opentelemetry_connection_string: str | None = "http://jaeger:4318/v1/traces"
    opentelemetry_sqlalchemy_min_query_duration_ms: int | None = 100

    msteams_notifications_webhook_url: str | None = None

    @computed_field
    def postgres_async_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_user,
            password=quote(self.postgres_password),
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )

    @computed_field
    def postgres_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.postgres_user,
            password=quote(self.postgres_password),
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )


_settings = None


def get_settings() -> Settings:
    global _settings
    if not _settings:
        _settings = Settings()
    return _settings

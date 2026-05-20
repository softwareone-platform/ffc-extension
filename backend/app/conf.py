import enum
import pathlib
from urllib.parse import quote

from pydantic import PostgresDsn, computed_field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent


class OpenTelemetryExporter(enum.StrEnum):
    JAEGER = "jaeger"
    AZURE_APP_INSIGHTS = "azure_app_insights"
    CONSOLE = "console"


#
#
# class Settings(BaseSettings):
#     """
#     Project settings loaded from environment variables
#     """
#
#     model_config = SettingsConfigDict(
#         env_file=PROJECT_ROOT / ".env",
#         env_file_encoding="utf-8",
#         env_prefix="ffc_ext_",
#         extra="ignore",
#     )
#
#     postgres_db: str
#     postgres_user: str
#     postgres_password: str
#     postgres_host: str
#     postgres_port: int = 5432
#
#     api_modifier_base_url: str
#     api_modifier_jwt_secret: str
#     secrets_encryption_key: str
#
#     datasources_expenses_obsolete_after_months: int = 6
#     billing_percentage: float = 1.0  # todo : ask if the default is 4 or 1.
#     ffc_external_product_id: str = "FIN-0001-P1M"
#
#     optscale_auth_api_base_url: str
#     optscale_rest_api_base_url: str
#     optscale_cluster_secret: str
#     optscale_read_timeout: int = 90
#
#     smtp_host: str
#     smtp_port: int = 587
#     smtp_user: str
#     smtp_password: str
#     smtp_sender_email: str
#     smtp_sender_name: str
#
#     mpt_api_base_url: str
#     mpt_extension_id: str
#     mpt_extension_token: str
#     mpt_product_id: str
#     mpt_api_rows_per_page: int = 100
#
#     exchange_rates_base_url: str
#     exchange_rates_api_token: str
#
#     api_base_url: str = "https://api.finops.softwareone.com/ops/v1"
#     cli_rich_logging: bool = True
#     debug: bool = False
#
#     opentelemetry_exporter: OpenTelemetryExporter | None = OpenTelemetryExporter.CONSOLE
#     opentelemetry_connection_string: str | None = "http://jaeger:4318/v1/traces"
#     opentelemetry_sqlalchemy_min_query_duration_ms: int | None = 100
#
#     msteams_notifications_webhook_url: str | None = None
#
#     ffc_billing_process_max_concurrency: int = 10
#     default_billed_percentage: int = 4
#     journal_validation_max_attempts: int = 5
#     default_trial_period_duration_days: int = 30
#     due_date_days: int = 30
#     # Billing command constraints
#     lower_billing_year: int = 2025
#
#     # def __init__(
#     #     __pydantic_self__,
#     #     _case_sensitive: bool | None = None,
#     #     _nested_model_default_partial_update: bool | None = None,
#     #     _env_prefix: str | None = None,
#     #     _env_prefix_target: EnvPrefixTarget | None = None,
#     #     _env_file: DotenvType | None = ENV_FILE_SENTINEL,
#     #     _env_file_encoding: str | None = None,
#     #     _env_ignore_empty: bool | None = None,
#     #     _env_nested_delimiter: str | None = None,
#     #     _env_nested_max_split: int | None = None,
#     #     _env_parse_none_str: str | None = None,
#     #     _env_parse_enums: bool | None = None,
#     #     _cli_prog_name: str | None = None,
#     #     _cli_parse_args: bool | list[str] | tuple[str, ...] | None = None,
#     #     _cli_settings_source: CliSettingsSource[Any] | None = None,
#     #     _cli_parse_none_str: str | None = None,
#     #     _cli_hide_none_type: bool | None = None,
#     #     _cli_avoid_json: bool | None = None,
#     #     _cli_enforce_required: bool | None = None,
#     #     _cli_use_class_docs_for_groups: bool | None = None,
#     #     _cli_exit_on_error: bool | None = None,
#     #     _cli_prefix: str | None = None,
#     #     _cli_flag_prefix_char: str | None = None,
#     #     _cli_implicit_flags: bool | Literal["dual", "toggle"] | None = None,
#     #     _cli_ignore_unknown_args: bool | None = None,
#     #     _cli_kebab_case: bool | Literal["all", "no_enums"] | None = None,
#     #     _cli_shortcuts: Mapping[str, str | list[str]] | None = None,
#     #     _secrets_dir: PathType | None = None,
#     #     _build_sources: tuple[tuple[PydanticBaseSettingsSource, ...], dict[str, Any]] |
#     None = None,
#     #     **values: Any,
#     # ):
#     #     super().__init__(
#     #         _case_sensitive,
#     #         _nested_model_default_partial_update,
#     #         _env_prefix,
#     #         _env_prefix_target,
#     #         _env_file,
#     #         _env_file_encoding,
#     #         _env_ignore_empty,
#     #         _env_nested_delimiter,
#     #         _env_nested_max_split,
#     #         _env_parse_none_str,
#     #         _env_parse_enums,
#     #         _cli_prog_name,
#     #         _cli_parse_args,
#     #         _cli_settings_source,
#     #         _cli_parse_none_str,
#     #         _cli_hide_none_type,
#     #         _cli_avoid_json,
#     #         _cli_enforce_required,
#     #         _cli_use_class_docs_for_groups,
#     #         _cli_exit_on_error,
#     #         _cli_prefix,
#     #         _cli_flag_prefix_char,
#     #         _cli_implicit_flags,
#     #         _cli_ignore_unknown_args,
#     #         _cli_kebab_case,
#     #         _cli_shortcuts,
#     #         _secrets_dir,
#     #         _build_sources,
#     #         values,
#     #     )
#     #     __pydantic_self__.product_id = None
#
#     @computed_field
#     def postgres_async_url(self) -> PostgresDsn:
#         return PostgresDsn.build(
#             scheme="postgresql+asyncpg",
#             username=self.postgres_user,
#             password=quote(self.postgres_password),
#             host=self.postgres_host,
#             port=self.postgres_port,
#             path=self.postgres_db,
#         )
#
#     @computed_field
#     def postgres_url(self) -> PostgresDsn:
#         return PostgresDsn.build(
#             scheme="postgresql",
#             username=self.postgres_user,
#             password=quote(self.postgres_password),
#             host=self.postgres_host,
#             port=self.postgres_port,
#             path=self.postgres_db,
#         )


class Settings(BaseSettings):
    """
    Project settings loaded from environment variables
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="ffc_ext_",
        extra="ignore",
    )

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432

    api_modifier_base_url: str
    api_modifier_jwt_secret: str

    datasources_expenses_obsolete_after_months: int = 6
    billing_percentage: float = 1.0  # todo : ask if the default is 4 or 1.
    ffc_external_product_id: str = "FIN-0001-P1M"

    optscale_auth_api_base_url: str
    optscale_rest_api_base_url: str
    optscale_cluster_secret: str
    optscale_read_timeout: int = 90

    mpt_api_base_url: str
    mpt_extension_id: str
    mpt_extension_token: str
    mpt_product_id: str
    mpt_api_rows_per_page: int = 100

    exchange_rates_base_url: str
    exchange_rates_api_token: str

    api_base_url: str = "https://api.finops.softwareone.com/ops/v1"
    cli_rich_logging: bool = True
    debug: bool = False

    opentelemetry_exporter: OpenTelemetryExporter | None = OpenTelemetryExporter.CONSOLE
    opentelemetry_connection_string: str | None = "http://jaeger:4318/v1/traces"
    opentelemetry_sqlalchemy_min_query_duration_ms: int | None = 100

    msteams_notifications_webhook_url: str | None = None

    ffc_billing_process_max_concurrency: int = 10
    default_billed_percentage: int = 4
    journal_validation_max_attempts: int = 5
    default_trial_period_duration_days: int = 30
    due_date_days: int = 30
    lower_billing_year: int = 2025

    ui_plugs_prefix: str = "ffc"

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

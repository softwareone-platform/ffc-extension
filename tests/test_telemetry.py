from pytest_mock import MockerFixture

from app.telemetry import (
    setup_fastapi_instrumentor,
    setup_sqlalchemy_instrumentor,
    setup_telemetry,
)


def test_setup_telemetry(mocker: MockerFixture):
    mock_settings = mocker.MagicMock()
    mock_settings.opentelemetry_exporter = "azure_app_insights"
    mock_settings.opentelemetry_connection_string = "mock_connection_string"
    mock_settings.opentelemetry_sqlalchemy_min_query_duration_ms = None
    mocked_exporter = mocker.MagicMock()
    mocked_tracer_provider = mocker.MagicMock()
    mocked_set_tracer_provider = mocker.patch(
        "app.telemetry.trace.set_tracer_provider",
    )
    mocked_exporter_ctor = mocker.patch(
        "app.telemetry.AzureMonitorTraceExporter",
        return_value=mocked_exporter,
    )
    mocked_batch_span_processor = mocker.MagicMock()
    mocked_batch_span_processor_ctor = mocker.patch(
        "app.telemetry.BatchSpanProcessor",
        return_value=mocked_batch_span_processor,
    )
    mocked_tracer_provider_ctor = mocker.patch(
        "app.telemetry.TracerProvider",
        return_value=mocked_tracer_provider,
    )
    mocked_instrument_httpx = mocker.MagicMock()
    mocked_instrument_httpx_ctor = mocker.patch(
        "app.telemetry.HTTPXClientInstrumentor",
        return_value=mocked_instrument_httpx,
    )
    mocked_instrument_logging = mocker.MagicMock()
    mocked_instrument_logging_ctor = mocker.patch(
        "app.telemetry.LoggingInstrumentor",
        return_value=mocked_instrument_logging,
    )
    setup_telemetry(mock_settings)

    mocked_exporter_ctor.assert_called_once_with(
        connection_string=mock_settings.opentelemetry_connection_string,
    )
    mocked_batch_span_processor_ctor.assert_called_once_with(mocked_exporter)
    mocked_tracer_provider_ctor.assert_called_once()
    mocked_tracer_provider.add_span_processor.assert_called_once_with(mocked_batch_span_processor)
    mocked_set_tracer_provider.assert_called_once_with(mocked_tracer_provider)
    mocked_instrument_httpx_ctor.assert_called_once()
    mocked_instrument_httpx.instrument.assert_called_once()
    mocked_instrument_logging_ctor.assert_called_once()
    mocked_instrument_logging.instrument.assert_called_once_with(set_logging_format=True)


def test_setup_telemetry_disabled(mocker: MockerFixture):
    mock_settings = mocker.MagicMock()
    mock_settings.opentelemetry_exporter = None
    mocked_exporter = mocker.MagicMock()
    mocked_tracer_provider = mocker.MagicMock()
    mocked_set_tracer_provider = mocker.patch(
        "app.telemetry.trace.set_tracer_provider",
    )
    mocked_exporter_ctor = mocker.patch(
        "app.telemetry.AzureMonitorTraceExporter",
        return_value=mocked_exporter,
    )
    mocked_batch_span_processor = mocker.MagicMock()
    mocked_batch_span_processor_ctor = mocker.patch(
        "app.telemetry.BatchSpanProcessor",
        return_value=mocked_batch_span_processor,
    )
    mocked_tracer_provider_ctor = mocker.patch(
        "app.telemetry.TracerProvider",
        return_value=mocked_tracer_provider,
    )
    mocked_instrument_httpx = mocker.MagicMock()
    mocked_instrument_httpx_ctor = mocker.patch(
        "app.telemetry.HTTPXClientInstrumentor",
        return_value=mocked_instrument_httpx,
    )
    mocked_instrument_logging = mocker.MagicMock()
    mocked_instrument_logging_ctor = mocker.patch(
        "app.telemetry.LoggingInstrumentor",
        return_value=mocked_instrument_logging,
    )
    setup_telemetry(mock_settings)

    mocked_exporter_ctor.assert_not_called()
    mocked_batch_span_processor_ctor.assert_not_called()
    mocked_tracer_provider_ctor.assert_not_called()
    mocked_set_tracer_provider.assert_not_called()
    mocked_instrument_httpx_ctor.assert_not_called()
    mocked_instrument_logging_ctor.assert_not_called()


def test_setup_fastapi_instrumentor(mocker: MockerFixture):
    mock_settings = mocker.MagicMock()
    mock_settings.opentelemetry_exporter = "azure_app_insights"
    mock_settings.opentelemetry_connection_string = "mock_connection_string"
    mocked_instrument_app = mocker.patch(
        "app.telemetry.FastAPIInstrumentor.instrument_app",
    )
    mocked_app = mocker.MagicMock()

    setup_fastapi_instrumentor(mock_settings, mocked_app)

    mocked_instrument_app.assert_called_once_with(mocked_app)


def test_setup_fastapi_instrumentor_disabled(mocker: MockerFixture):
    mock_settings = mocker.MagicMock()
    mock_settings.opentelemetry_exporter = None
    mocked_instrument_app = mocker.patch(
        "app.telemetry.FastAPIInstrumentor.instrument_app",
    )
    mocked_app = mocker.MagicMock()

    setup_fastapi_instrumentor(mock_settings, mocked_app)

    mocked_instrument_app.assert_not_called()


def test_setup_sqlalchemy_instrumentor(mocker: MockerFixture):
    mock_settings = mocker.MagicMock()
    mock_settings.opentelemetry_exporter = "azure_app_insights"
    mock_settings.opentelemetry_connection_string = "mock_connection_string"
    mocked_instrument_sqlalchemy = mocker.MagicMock()
    mocker.patch(
        "app.telemetry.SQLAlchemyInstrumentor",
        return_value=mocked_instrument_sqlalchemy,
    )
    mocked_dbengine = mocker.MagicMock()

    setup_sqlalchemy_instrumentor(mock_settings, mocked_dbengine)

    mocked_instrument_sqlalchemy.instrument.assert_called_once_with(
        engine=mocked_dbengine.sync_engine,
        enable_commenter=True,
    )


def test_setup_sqlalchemy_disabled(mocker: MockerFixture):
    mock_settings = mocker.MagicMock()
    mock_settings.opentelemetry_exporter = None
    mocked_instrument_sqlalchemy = mocker.MagicMock()
    mocker.patch(
        "app.telemetry.SQLAlchemyInstrumentor",
        return_value=mocked_instrument_sqlalchemy,
    )
    mocked_dbengine = mocker.MagicMock()

    setup_sqlalchemy_instrumentor(mock_settings, mocked_dbengine)

    mocked_instrument_sqlalchemy.instrument.assert_not_called()

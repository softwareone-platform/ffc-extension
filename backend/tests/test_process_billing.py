import hashlib
import json
import logging
import tempfile
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from app.billing.dataclasses import CurrencyConversionInfo, ProcessResultInfo, Refund
from app.billing.enum import ProcessResult
from app.billing.exceptions import (
    ExchangeRatesClientError,
    JournalStatusError,
    JournalSubmitError,
)
from app.billing.process_billing import (
    AuthorizationProcessor,
    get_billing_percentage,
    get_trial_dates,
    process_billing,
    split_entitlement_days_into_ranges,
)
from app.conf import Settings
from app.db.models import Entitlement, Organization
from app.enums import DatasourceType, EntitlementStatus
from tests.types import ModelFactory

AUTHORIZATION = {
    "id": "AUT-5305-9928",
    "name": "TEST",
    "currency": "USD",
}


# ----------------------------------------------------------------------------------
# - process_billing()
# ----------------------------------------------------------------------------------


async def test_process_billing_with_single_authorization(
    mocker: MockerFixture, httpx_mock: HTTPXMock
) -> None:
    """When started with an authorization id, it fetches that authorization and
    runs a single AuthorizationProcessor."""
    mock_processor_cls = mocker.patch("app.billing.process_billing.AuthorizationProcessor")
    mock_processor_cls.return_value.process = AsyncMock()
    mock_notify = mocker.patch(
        "app.billing.process_billing.send_notifications", new_callable=AsyncMock
    )
    httpx_mock.add_response(method="GET", json={"id": "AUTH1"})

    await process_billing(2025, 7, 5, "AUTH1", dry_run=True)

    mock_processor_cls.assert_called_once_with(2025, 7, {"id": "AUTH1"}, True)
    mock_processor_cls.return_value.process.assert_awaited_once()
    mock_notify.assert_awaited_once()


async def test_process_billing_with_multiple_authorizations(
    mocker: MockerFixture, httpx_mock: HTTPXMock
) -> None:
    """When started without an authorization id, every authorization for the product
    is processed and a notification is sent."""
    mock_processor_cls = mocker.patch("app.billing.process_billing.AuthorizationProcessor")
    mock_processor_cls.return_value.process = AsyncMock()
    mock_notify = mocker.patch(
        "app.billing.process_billing.send_notifications", new_callable=AsyncMock
    )
    httpx_mock.add_response(
        method="GET",
        json={
            "data": [{"id": "AUTH1"}, {"id": "AUTH2"}],
            "$meta": {"pagination": {"total": 2}},
        },
    )

    await process_billing(2025, 7, cutoff_day=5)

    assert mock_processor_cls.call_count == 2
    assert mock_processor_cls.return_value.process.await_count == 2
    mock_notify.assert_awaited_once()
    _, kwargs = mock_notify.call_args
    assert kwargs["year"] == 2025
    assert kwargs["month"] == 7
    assert kwargs["cutoff_day"] == 5


# ----------------------------------------------------------------------------------
# - AuthorizationProcessor.process()
# ----------------------------------------------------------------------------------


async def test_process_no_active_agreements(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
) -> None:
    """If there are no active agreements, the journal is skipped."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json={"$meta": {"pagination": {"total": 0}}})

    with caplog.at_level(logging.INFO):
        response = await processor.process()

    assert isinstance(response, ProcessResultInfo)
    assert response.result == ProcessResult.JOURNAL_SKIPPED
    assert response.message == "No active agreement for authorization AUT-5305-9928"


async def test_process_success(httpx_mock: HTTPXMock, mocker: MockerFixture) -> None:
    """The happy path: charges are written and the journal is completed."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json={"$meta": {"pagination": {"total": 2}}})
    evaluate = mocker.patch.object(processor, "evaluate_journal_status", return_value=None)
    write = mocker.patch.object(processor, "write_charges_file", return_value=True)
    complete = mocker.patch.object(processor, "complete_journal_process", return_value=None)

    response = await processor.process()

    assert response.result == ProcessResult.JOURNAL_GENERATED
    evaluate.assert_awaited_once()
    write.assert_awaited_once()
    complete.assert_awaited_once()


async def test_process_journal_already_validated(
    httpx_mock: HTTPXMock, mocker: MockerFixture, existing_journal_file_response: dict
) -> None:
    """If an existing journal is already Validated, it is submitted and generated."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    journal = existing_journal_file_response["data"][0]
    journal["status"] = "Validated"
    httpx_mock.add_response(method="GET", json={"$meta": {"pagination": {"total": 2}}})
    httpx_mock.add_response(method="POST", status_code=200)
    mocker.patch.object(processor, "evaluate_journal_status", return_value=journal)

    response = await processor.process()

    assert response.result == ProcessResult.JOURNAL_GENERATED
    assert response.journal_id == "BJO-9000-4019"


async def test_process_existing_journal_non_draft_skips(
    httpx_mock: HTTPXMock, mocker: MockerFixture, existing_journal_file_response: dict
) -> None:
    """If an existing journal is neither Validated nor Draft, the flow is skipped."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    journal = existing_journal_file_response["data"][0]
    journal["status"] = "Review"
    httpx_mock.add_response(method="GET", json={"$meta": {"pagination": {"total": 2}}})
    mocker.patch.object(processor, "evaluate_journal_status", return_value=journal)

    response = await processor.process()

    assert response.result == ProcessResult.JOURNAL_SKIPPED
    assert response.journal_id == "BJO-9000-4019"


async def test_process_no_charges_written(httpx_mock: HTTPXMock, mocker: MockerFixture) -> None:
    """If no charges are written, the journal is skipped and not completed."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json={"$meta": {"pagination": {"total": 2}}})
    mocker.patch.object(processor, "evaluate_journal_status", return_value=None)
    mocker.patch.object(processor, "write_charges_file", return_value=False)
    complete = mocker.patch.object(processor, "complete_journal_process", return_value=None)

    response = await processor.process()

    assert response.result == ProcessResult.JOURNAL_SKIPPED
    assert response.message == "No charges for this authorization."
    complete.assert_not_awaited()


async def test_process_http_status_error_with_json(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
) -> None:
    """An HTTP error with a JSON body is logged with the decoded reason."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", status_code=400, json={"error": "Invalid request"})

    with caplog.at_level(logging.ERROR):
        response = await processor.process()

    assert response.result == ProcessResult.ERROR
    assert "[AUT-5305-9928] 400 " in caplog.messages[0]


async def test_process_http_status_error_without_json(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
) -> None:
    """An HTTP error with a non-JSON body is logged with the decoded content."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(
        method="GET",
        status_code=400,
        content=b'{"error": "Invalid request"}',
        headers={"Content-Type": "application/text"},
    )

    with caplog.at_level(logging.ERROR):
        response = await processor.process()

    assert response.result == ProcessResult.ERROR
    assert "[AUT-5305-9928] 400 " in caplog.messages[0]


async def test_process_generic_exception(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Any other exception is logged and reported as an error."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_exception(Exception("No good Reasons"))

    with caplog.at_level(logging.ERROR):
        response = await processor.process()

    assert response.result == ProcessResult.ERROR
    assert "[AUT-5305-9928] An error occurred: No good Reasons" in caplog.messages[0]


async def test_process_journal_status_error(httpx_mock: HTTPXMock, mocker: MockerFixture) -> None:
    """A JournalStatusError while evaluating the journal results in a skip."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json={"$meta": {"pagination": {"total": 2}}})
    mocker.patch.object(
        processor,
        "evaluate_journal_status",
        side_effect=JournalStatusError("an error occurred.", journal_id="BJO-9000-4019"),
    )

    response = await processor.process()

    assert response.result is ProcessResult.JOURNAL_SKIPPED
    assert response.journal_id == "BJO-9000-4019"
    assert response.message == "an error occurred."


async def test_process_journal_submit_error(httpx_mock: HTTPXMock, mocker: MockerFixture) -> None:
    """A JournalSubmitError while writing charges is reported as an error."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json={"$meta": {"pagination": {"total": 2}}})
    mocker.patch.object(processor, "evaluate_journal_status", return_value=None)
    mocker.patch.object(
        processor,
        "write_charges_file",
        side_effect=JournalSubmitError("an error occurred.", journal_id="BJO-9000-4019"),
    )

    response = await processor.process()

    assert response.result is ProcessResult.ERROR
    assert response.journal_id == "BJO-9000-4019"
    assert response.message == "an error occurred."


# ----------------------------------------------------------------------------------
# - evaluate_journal_status()
# ----------------------------------------------------------------------------------


async def test_evaluate_journal_status_draft(
    httpx_mock: HTTPXMock, existing_journal_file_response: dict, caplog: pytest.LogCaptureFixture
) -> None:
    """A Draft journal is returned as is."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json=existing_journal_file_response)

    with caplog.at_level(logging.INFO):
        result = await processor.evaluate_journal_status(journal_external_id="202505")

    assert result == existing_journal_file_response["data"][0]
    assert "[AUT-5305-9928] Already found journal: BJO-9000-4019 with status Draft" in caplog.text


async def test_evaluate_journal_status_validated(
    httpx_mock: HTTPXMock, existing_journal_file_response: dict, caplog: pytest.LogCaptureFixture
) -> None:
    """A Validated journal is returned as is."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    existing_journal_file_response["data"][0]["status"] = "Validated"
    httpx_mock.add_response(method="GET", json=existing_journal_file_response)

    with caplog.at_level(logging.INFO):
        result = await processor.evaluate_journal_status(journal_external_id="202505")

    assert result == existing_journal_file_response["data"][0]
    assert (
        "[AUT-5305-9928] Already found journal: BJO-9000-4019 with status Validated" in caplog.text
    )


async def test_evaluate_journal_status_raises_on_disallowed_valid_status(
    httpx_mock: HTTPXMock, existing_journal_file_response: dict, caplog: pytest.LogCaptureFixture
) -> None:
    """A journal with a valid status that is not allowed raises a JournalStatusError."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    existing_journal_file_response["data"][0]["status"] = "Review"
    httpx_mock.add_response(method="GET", json=existing_journal_file_response)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(JournalStatusError) as exc_info:
            await processor.evaluate_journal_status(journal_external_id="202505")

    assert "Found the journal BJO-9000-4019 with invalid status Review" in caplog.text
    assert exc_info.value.journal_id == "BJO-9000-4019"


async def test_evaluate_journal_status_raises_on_unparseable_status(
    httpx_mock: HTTPXMock, existing_journal_file_response: dict, caplog: pytest.LogCaptureFixture
) -> None:
    """A journal with an unknown status raises a JournalStatusError."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    existing_journal_file_response["data"][0]["status"] = "Another Status"
    httpx_mock.add_response(method="GET", json=existing_journal_file_response)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(JournalStatusError):
            await processor.evaluate_journal_status(journal_external_id="202505")

    assert (
        "[AUT-5305-9928] Found the journal BJO-9000-4019 with status Another Status" in caplog.text
    )


async def test_evaluate_journal_status_returns_none_when_not_found(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
) -> None:
    """If no journal is found, None is returned."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json={"data": []})

    with caplog.at_level(logging.INFO):
        result = await processor.evaluate_journal_status(journal_external_id="202505")

    assert result is None
    assert "[AUT-5305-9928] No journal found for external ID: 202505" in caplog.text


# ----------------------------------------------------------------------------------
# - is_journal_status_validated()
# ----------------------------------------------------------------------------------


async def test_is_journal_status_validated_success(
    httpx_mock: HTTPXMock, existing_journal_file_response: dict
) -> None:
    """If the journal is Validated, the method returns True."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    journal = existing_journal_file_response["data"][0]
    journal["status"] = "Validated"
    httpx_mock.add_response(method="GET", json=journal)

    result = await processor.is_journal_status_validated(journal_id=journal["id"])

    assert result is True


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
async def test_is_journal_status_validated_fail_and_retry(
    httpx_mock: HTTPXMock, mocker: MockerFixture, existing_journal_file_response: dict
) -> None:
    """If the journal never validates, it retries the default number of attempts."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    journal = existing_journal_file_response["data"][0]
    httpx_mock.add_response(method="GET", json=journal)
    mocker.patch("app.billing.process_billing.asyncio.sleep", return_value=None)

    result = await processor.is_journal_status_validated(journal_id=journal["id"])

    assert result is False
    assert len(httpx_mock.get_requests()) == 5


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
async def test_is_journal_status_validated_uses_default_max_attempts(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    """If max_attempts is not provided, the configured default is used."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json={"status": "Draft"})
    mocker.patch("app.billing.process_billing.asyncio.sleep", return_value=None)
    mocker.patch.object(processor.settings, "journal_validation_max_attempts", 3)

    result = await processor.is_journal_status_validated("BJO-9000-4019")

    assert result is False
    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
async def test_is_journal_status_validated_logs_warning_on_exception(
    httpx_mock: HTTPXMock, mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    """Exceptions during the check are logged as warnings without breaking the loop."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_exception(Exception("temporary error"))
    mocker.patch("app.billing.process_billing.asyncio.sleep", return_value=None)

    with caplog.at_level(logging.WARNING):
        result = await processor.is_journal_status_validated("BJO-9000-4019", max_attempts=2)

    assert result is False
    assert len(httpx_mock.get_requests()) == 2
    assert "Error checking journal status on attempt 1: temporary error" in caplog.text


# ----------------------------------------------------------------------------------
# - write_charges_file()
# ----------------------------------------------------------------------------------


async def test_write_charges_file_writes_lines(
    db_session,
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    organization_factory: ModelFactory[Organization],
    datasource_expense_factory: ModelFactory,
    temp_charges_file: str,
) -> None:
    """When an organization has a single matching agreement and expenses, charges are written."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    org = await organization_factory(billing_currency="USD")
    await datasource_expense_factory(organization=org, year=2025, month=6)
    httpx_mock.add_response(
        method="GET",
        json={
            "data": [{"authorization": {"id": "AUT-5305-9928"}}],
            "$meta": {"pagination": {"total": 1}},
        },
    )
    mocker.patch.object(
        processor,
        "generate_datasource_charges",
        return_value=['{"id": 1, "name": "test_1"}\n', '{"id": 2, "name": "test_2"}\n'],
    )

    result = await processor.write_charges_file(filepath=temp_charges_file)

    assert result is True


async def test_write_charges_file_empty_when_no_expenses(
    db_session,
    httpx_mock: HTTPXMock,
    organization_factory: ModelFactory[Organization],
    temp_charges_file: str,
) -> None:
    """With no expenses nothing is written and the method returns False."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    await organization_factory(billing_currency="USD")
    httpx_mock.add_response(
        method="GET",
        json={
            "data": [{"authorization": {"id": "AUT-5305-9928"}}],
            "$meta": {"pagination": {"total": 1}},
        },
    )

    result = await processor.write_charges_file(filepath=temp_charges_file)

    assert result is False


async def test_write_charges_file_skips_operations_skip_id(
    db_session,
    organization_factory: ModelFactory[Organization],
    temp_charges_file: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Organizations flagged with the skip operations id are ignored."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    org = await organization_factory(
        billing_currency="USD", operations_external_id="AGR-0000-0000-0000"
    )

    with caplog.at_level(logging.INFO):
        result = await processor.write_charges_file(filepath=temp_charges_file)

    assert result is False
    assert (
        f"[AUT-5305-9928] Skip organization {org.id} - {org.name} "
        "because of ID AGR-0000-0000-0000" in caplog.text
    )


async def test_write_charges_file_skips_when_multiple_agreements(
    db_session,
    httpx_mock: HTTPXMock,
    organization_factory: ModelFactory[Organization],
    temp_charges_file: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Organizations with more than one agreement are skipped as invalid."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    org = await organization_factory(billing_currency="USD")
    httpx_mock.add_response(
        method="GET",
        json={
            "data": [
                {"authorization": {"id": "AUT-5305-9928"}},
                {"authorization": {"id": "AUT-5305-9928"}},
            ],
            "$meta": {"pagination": {"total": 2}},
        },
    )

    with caplog.at_level(logging.INFO):
        result = await processor.write_charges_file(filepath=temp_charges_file)

    assert result is False
    assert (
        f"[AUT-5305-9928] Found 2 while we were expecting 1 for the organization {org.id}"
        in caplog.text
    )


async def test_write_charges_file_skips_other_authorization(
    db_session,
    httpx_mock: HTTPXMock,
    organization_factory: ModelFactory[Organization],
    temp_charges_file: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Agreements belonging to a different authorization are skipped."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    org = await organization_factory(billing_currency="USD")
    httpx_mock.add_response(
        method="GET",
        json={
            "data": [{"authorization": {"id": "AUT-5305-9955"}}],
            "$meta": {"pagination": {"total": 1}},
        },
    )

    with caplog.at_level(logging.INFO):
        result = await processor.write_charges_file(filepath=temp_charges_file)

    assert result is False
    assert (
        f"[AUT-5305-9928] Skipping organization {org.id} because it belongs "
        "to an agreement with different authorization: AUT-5305-9955" in caplog.text
    )


# ----------------------------------------------------------------------------------
# - complete_journal_process()
# ----------------------------------------------------------------------------------


async def test_complete_journal_process_success(
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    test_settings: Settings,
    create_journal_response: dict,
    temp_charges_file: str,
    exchange_rates: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A new journal is created, attachments uploaded, and the validated journal submitted."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    base_url = test_settings.mpt_api_base_url
    create_journal_response["status"] = "Validated"
    processor.exchange_rates = exchange_rates
    mocker.patch.object(processor, "attach_exchange_rates", return_value=None)
    mocker.patch.object(processor, "is_journal_status_validated", return_value=True)
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/billing/journals", json=create_journal_response
    )
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/billing/journals/BJO-9000-4019/upload", status_code=200
    )
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/billing/journals/BJO-9000-4019/submit", status_code=200
    )

    with caplog.at_level(logging.INFO):
        response = await processor.complete_journal_process(
            filepath=temp_charges_file,
            journal=None,
            journal_external_id="BJO-9000-4019",
        )

    assert response == create_journal_response
    assert "[AUT-5305-9928] new journal created: BJO-9000-4019" in caplog.text
    assert "[AUT-5305-9928] submitting the journal BJO-9000-4019." in caplog.text


async def test_complete_journal_process_not_validated_raises(
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    test_settings: Settings,
    create_journal_response: dict,
    temp_charges_file: str,
    exchange_rates: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If the journal does not become validated, a JournalSubmitError is raised."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    base_url = test_settings.mpt_api_base_url
    processor.exchange_rates = exchange_rates
    mocker.patch.object(processor, "attach_exchange_rates", return_value=None)
    mocker.patch.object(processor, "is_journal_status_validated", return_value=False)
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/billing/journals/BJO-9000-4019/upload", status_code=200
    )

    with caplog.at_level(logging.INFO):
        with pytest.raises(JournalSubmitError):
            await processor.complete_journal_process(
                filepath=temp_charges_file,
                journal=create_journal_response,
                journal_external_id="BJO-9000-4019",
            )

    assert (
        "[AUT-5305-9928] cannot submit the journal BJO-9000-4019 it doesn't get validated"
        in caplog.text
    )


# ----------------------------------------------------------------------------------
# - attach_exchange_rates()
# ----------------------------------------------------------------------------------


async def test_attach_exchange_rates_no_existing_attachment(
    httpx_mock: HTTPXMock, exchange_rates: dict
) -> None:
    """With no existing attachment, a new one is created."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json={"data": []})
    httpx_mock.add_response(method="POST", status_code=201)

    await processor.attach_exchange_rates(
        journal_id="BJO-9000-4019", currency="EUR", exchange_rates=exchange_rates
    )


async def test_attach_exchange_rates_existing_attachment_same_name(
    httpx_mock: HTTPXMock, exchange_rates: dict
) -> None:
    """If the existing attachment already matches the filename, nothing is changed."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    serialized = json.dumps(exchange_rates)
    filename = f"EUR_{hashlib.sha256(serialized.encode()).hexdigest()}"
    httpx_mock.add_response(
        method="GET", json={"data": [{"id": "JOA-5985-1983", "name": filename}]}
    )

    await processor.attach_exchange_rates(
        journal_id="BJO-9000-4019", currency="EUR", exchange_rates=exchange_rates
    )


async def test_attach_exchange_rates_existing_attachment_different_name(
    httpx_mock: HTTPXMock, exchange_rates: dict
) -> None:
    """If the existing attachment differs, it is deleted and a new one created."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(
        method="GET", json={"data": [{"id": "JOA-5985-1983", "name": "EUR_oldhash"}]}
    )
    httpx_mock.add_response(method="DELETE", status_code=204)
    httpx_mock.add_response(method="POST", status_code=201)

    await processor.attach_exchange_rates(
        journal_id="BJO-9000-4019", currency="EUR", exchange_rates=exchange_rates
    )


# ----------------------------------------------------------------------------------
# - get_currency_conversion_info()
# ----------------------------------------------------------------------------------


async def test_get_currency_conversion_info_raises_for_missing_org_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing organization attributes are logged and re-raised as AttributeError."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    invalid_organization = SimpleNamespace(
        id="FORG-1234",
        name="Test Org",
        operations_external_id="AGR-1234-5678-9012",
        currency="USD",
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(AttributeError):
            await processor.get_currency_conversion_info(organization=invalid_organization)

    assert "Missing required attribute in organization" in caplog.text


async def test_get_currency_conversion_info_needed(
    httpx_mock: HTTPXMock,
    build_test_organization: Organization,
    exchange_rates: dict,
    currency_conversion: dict,
) -> None:
    """When currencies differ, the exchange rates are fetched for the conversion."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json=exchange_rates)

    result = await processor.get_currency_conversion_info(organization=build_test_organization)

    assert isinstance(result, CurrencyConversionInfo)
    assert result.__dict__ == currency_conversion


async def test_get_currency_conversion_info_not_needed(
    build_test_organization: Organization, caplog: pytest.LogCaptureFixture
) -> None:
    """When data and billing currency match, no conversion is needed."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    build_test_organization.billing_currency = "USD"

    with caplog.at_level(logging.INFO):
        result = await processor.get_currency_conversion_info(organization=build_test_organization)

    assert isinstance(result, CurrencyConversionInfo)
    assert (
        f"[AUT-5305-9928] organization {build_test_organization.id} - "
        f"{build_test_organization.name} doesn't need currency conversion" in caplog.messages[0]
    )


async def test_get_currency_conversion_info_raises_on_empty_rates(
    httpx_mock: HTTPXMock, build_test_organization: Organization, caplog: pytest.LogCaptureFixture
) -> None:
    """An empty exchange-rates response raises an ExchangeRatesClientError."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    build_test_organization.billing_currency = "EUR"
    httpx_mock.add_response(method="GET", json={})

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ExchangeRatesClientError):
            await processor.get_currency_conversion_info(organization=build_test_organization)

    assert (
        "[AUT-5305-9928] An error occurred while fetching exchange rates for USD"
        in caplog.messages[0]
    )


async def test_get_currency_conversion_info_raises_on_missing_conversion_rate(
    httpx_mock: HTTPXMock, build_test_organization: Organization, caplog: pytest.LogCaptureFixture
) -> None:
    """A malformed exchange-rates structure raises an ExchangeRatesClientError."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    build_test_organization.billing_currency = "EUR"
    httpx_mock.add_response(method="GET", json={"result": "success"})

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ExchangeRatesClientError):
            await processor.get_currency_conversion_info(organization=build_test_organization)

    assert "Invalid exchange rates response structure for" in caplog.text


# ----------------------------------------------------------------------------------
# - generate_datasource_charges()
# ----------------------------------------------------------------------------------


async def test_generate_datasource_charges_empty_daily_expenses(
    build_test_organization: Organization, agreement_data_no_trial
) -> None:
    """With no daily expenses a single zero charge line is produced."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    agreement_data = agreement_data_no_trial()

    response = await processor.generate_datasource_charges(
        organization=build_test_organization,
        agreement=agreement_data[0],
        linked_datasource_id="34654563456",
        linked_datasource_type="aws_cnr",
        datasource_id="1234",
        datasource_name="Test",
        daily_expenses={},
    )

    assert isinstance(response[0], str)
    line = json.loads(response[0])
    assert line == {
        "externalIds": {"vendor": "34654563456-01", "invoice": "-", "reference": "1234"},
        "search": {
            "source": {
                "type": "Subscription",
                "criteria": "externalIds.vendor",
                "value": "FORG-4801-6958-2949",
            },
            "item": {"criteria": "item.externalIds.vendor", "value": "FIN-0001-P1M"},
        },
        "period": {"start": "2025-06-01T00:00:00+00:00", "end": "2025-06-30T23:59:59+00:00"},
        "price": {"unitPP": "0.0000", "PPx1": "0.0000"},
        "quantity": 1,
        "description": {
            "value1": "Amazon Web Services datasource with name Test and id 1234",
            "value2": "No charges available for this datasource.",
        },
        "segment": "COM",
    }


async def test_generate_datasource_charges_price_in_source_currency_eq_0(
    build_test_organization: Organization,
    daily_expenses: dict,
    agreement_data_with_trial,
) -> None:
    """If the billed percentage is zero, a single zero charge line is produced."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    data = agreement_data_with_trial(
        parameters={
            "fulfillment": [
                {
                    "id": "PAR-7208-0459-0011",
                    "externalId": "billedPercentage",
                    "name": "Billed percentage of monthly spend",
                    "type": "SingleLineText",
                    "phase": "Fulfillment",
                    "displayValue": "0",
                    "value": "0",
                }
            ]
        }
    )

    response = await processor.generate_datasource_charges(
        organization=build_test_organization,
        agreement=data[0],
        linked_datasource_id="34654563456",
        linked_datasource_type="aws_cnr",
        datasource_id="34654563488",
        datasource_name="Test",
        daily_expenses=daily_expenses,
    )

    assert isinstance(response[0], str)
    line = json.loads(response[0])
    assert line["price"] == {"unitPP": "0.0000", "PPx1": "0.0000"}
    assert line["period"] == {
        "start": "2025-06-01T00:00:00+00:00",
        "end": "2025-06-30T23:59:59+00:00",
    }
    assert line["description"]["value2"] == ""


async def test_generate_datasource_charges_stores_exchange_rates_by_base_currency(
    build_test_organization: Organization, mocker: MockerFixture
) -> None:
    """When conversion info includes exchange rates, they are cached by base currency."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    mocker.patch.object(processor, "generate_refund_lines", return_value=[])
    mocker.patch.object(
        processor,
        "get_currency_conversion_info",
        return_value=CurrencyConversionInfo(
            base_currency="USD",
            billing_currency="EUR",
            exchange_rate=Decimal("1.1000"),
            exchange_rates={"conversion_rates": {"EUR": 1.1}},
        ),
    )

    await processor.generate_datasource_charges(
        organization=build_test_organization,
        agreement={
            "parameters": {"fulfillment": [{"externalId": "billedPercentage", "value": "4"}]}
        },
        linked_datasource_id="34654563456",
        linked_datasource_type="aws_cnr",
        datasource_id="ds-1",
        datasource_name="DS One",
        daily_expenses={1: Decimal("100")},
    )

    assert processor.exchange_rates["USD"] == {"conversion_rates": {"EUR": 1.1}}


async def test_generate_datasource_charges_without_exchange_rates_not_cached(
    build_test_organization: Organization, mocker: MockerFixture
) -> None:
    """When conversion info carries no exchange rates, nothing is cached."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    mocker.patch.object(processor, "generate_refund_lines", return_value=[])
    mocker.patch.object(
        processor,
        "get_currency_conversion_info",
        return_value=CurrencyConversionInfo(
            base_currency="USD",
            billing_currency="EUR",
            exchange_rate=Decimal("1.1000"),
            exchange_rates=None,
        ),
    )

    await processor.generate_datasource_charges(
        organization=build_test_organization,
        agreement={
            "parameters": {"fulfillment": [{"externalId": "billedPercentage", "value": "4"}]}
        },
        linked_datasource_id="34654563456",
        linked_datasource_type="aws_cnr",
        datasource_id="ds-1",
        datasource_name="DS One",
        daily_expenses={1: Decimal("100")},
    )

    assert "USD" not in processor.exchange_rates


async def test_generate_datasource_charges_no_entitlement(
    httpx_mock: HTTPXMock,
    build_test_organization: Organization,
    agreement_data_with_trial,
    daily_expenses: dict,
    exchange_rates: dict,
) -> None:
    """With no entitlement, the main charge and the trial refund are produced."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    httpx_mock.add_response(method="GET", json=exchange_rates)
    agreement_data = agreement_data_with_trial()

    response = await processor.generate_datasource_charges(
        organization=build_test_organization,
        agreement=agreement_data[0],
        linked_datasource_id="34654563456",
        linked_datasource_type="aws_cnr",
        datasource_id="34654563488",
        datasource_name="Test",
        daily_expenses=daily_expenses,
    )

    lines = [json.loads(r) for r in response]
    assert lines[0]["price"] == {"unitPP": "183.9829", "PPx1": "183.9829"}
    assert lines[0]["period"] == {
        "start": "2025-06-01T00:00:00+00:00",
        "end": "2025-06-30T23:59:59+00:00",
    }
    assert lines[1]["price"] == {"unitPP": "-39.1447", "PPx1": "-39.1447"}
    assert lines[1]["period"] == {
        "start": "2025-06-01T00:00:00+00:00",
        "end": "2025-06-15T23:59:59+00:00",
    }
    assert (
        lines[1]["description"]["value2"]
        == "Refund due to trial period (from 01 Jun 2025 to 15 Jun 2025)"
    )


async def test_generate_datasource_charges_active_trial_and_terminated_entitlement(
    db_session,
    httpx_mock: HTTPXMock,
    organization_factory: ModelFactory[Organization],
    entitlement_factory: ModelFactory[Entitlement],
    agreement_data_with_trial,
    daily_expenses: dict,
    exchange_rates: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A terminated entitlement produces an additional refund line for its active days."""
    processor = AuthorizationProcessor(year=2025, month=9, authorization=AUTHORIZATION)
    org = await organization_factory(currency="USD", billing_currency="EUR")
    entitlement = await entitlement_factory(
        datasource_id="34654563488",
        linked_datasource_type=DatasourceType.AWS_CNR,
        status=EntitlementStatus.ACTIVE,
        redeemed_by=org,
        redeemed_at=datetime(2025, 9, 6, 8, 39, 45, 995072, tzinfo=UTC),
        terminated_at=datetime(2025, 9, 28, 7, 47, 19, 142190, tzinfo=UTC),
    )
    httpx_mock.add_response(method="GET", json=exchange_rates)
    agreement = agreement_data_with_trial(
        parameters={
            "fulfillment": [
                {"externalId": "trialStartDate", "value": "2025-08-27"},
                {"externalId": "trialEndDate", "value": "2025-09-15"},
                {"externalId": "billedPercentage", "value": "4"},
            ]
        }
    )

    with caplog.at_level(logging.INFO):
        response = await processor.generate_datasource_charges(
            organization=org,
            agreement=agreement[0],
            linked_datasource_id="34654563456",
            linked_datasource_type="aws_cnr",
            datasource_id="34654563488",
            datasource_name="Test",
            daily_expenses=daily_expenses,
        )

    lines = [json.loads(r) for r in response]
    assert lines[0]["price"] == {"unitPP": "183.9829", "PPx1": "183.9829"}
    assert lines[0]["search"]["source"]["value"] == org.id
    assert lines[1]["period"] == {
        "start": "2025-09-01T00:00:00+00:00",
        "end": "2025-09-15T23:59:59+00:00",
    }
    assert lines[1]["price"] == {"unitPP": "-39.1447", "PPx1": "-39.1447"}
    assert (
        lines[1]["description"]["value2"]
        == "Refund due to trial period (from 27 Aug 2025 to 15 Sep 2025)"
    )
    assert lines[2]["period"] == {
        "start": "2025-09-16T00:00:00+00:00",
        "end": "2025-09-28T23:59:59+00:00",
    }
    assert lines[2]["price"] == {"unitPP": "-137.9294", "PPx1": "-137.9294"}
    assert lines[2]["description"]["value2"] == (
        f"Refund due to active entitlement {entitlement.id}"
    )
    assert (
        f"[AUT-5305-9928] : organization_id='{org.id}'"
        " linked_datasource_id='34654563456' datasource_name='Test' - "
        "amount=Decimal('5326.0458') billing_percentage=Decimal('4') "
        "price_in_source_currency=Decimal('213.0418') "
        "exchange_rate=Decimal('0.8636') price_in_target_currency=Decimal('183.98289848')"
        in caplog.text
    )


async def test_generate_datasource_charges_active_trial_and_active_entitlement(
    db_session,
    httpx_mock: HTTPXMock,
    organization_factory: ModelFactory[Organization],
    entitlement_factory: ModelFactory[Entitlement],
    agreement_data_with_trial,
    daily_expenses: dict,
    exchange_rates: dict,
) -> None:
    """An active entitlement overlapping a long trial still yields the main and trial lines."""
    processor = AuthorizationProcessor(year=2025, month=9, authorization=AUTHORIZATION)
    org = await organization_factory(currency="USD", billing_currency="EUR")
    await entitlement_factory(
        datasource_id="34654563488",
        linked_datasource_type=DatasourceType.AWS_CNR,
        status=EntitlementStatus.ACTIVE,
        redeemed_by=org,
        redeemed_at=datetime(2025, 9, 6, 8, 39, 45, 995072, tzinfo=UTC),
    )
    httpx_mock.add_response(method="GET", json=exchange_rates)
    agreement = agreement_data_with_trial(
        parameters={
            "fulfillment": [
                {"externalId": "trialStartDate", "value": "2025-08-27"},
                {"externalId": "trialEndDate", "value": "2025-09-26"},
                {"externalId": "billedPercentage", "value": "4"},
            ]
        }
    )

    response = await processor.generate_datasource_charges(
        organization=org,
        agreement=agreement[0],
        linked_datasource_id="34654563456",
        linked_datasource_type="aws_cnr",
        datasource_id="34654563488",
        datasource_name="Test",
        daily_expenses=daily_expenses,
    )

    lines = [json.loads(r) for r in response]
    assert lines[0]["price"] == {"unitPP": "183.9829", "PPx1": "183.9829"}
    assert lines[0]["search"]["source"]["value"] == org.id
    assert lines[1]["period"] == {
        "start": "2025-09-01T00:00:00+00:00",
        "end": "2025-09-26T23:59:59+00:00",
    }
    assert lines[1]["price"] == {"unitPP": "-153.1250", "PPx1": "-153.1250"}
    assert (
        lines[1]["description"]["value2"]
        == "Refund due to trial period (from 27 Aug 2025 to 26 Sep 2025)"
    )


# ----------------------------------------------------------------------------------
# - generate_refunds()
# ----------------------------------------------------------------------------------


def test_generate_refunds_trial_only(daily_expenses: dict, agreement_data_with_trial) -> None:
    """A trial that overlaps the billing period produces a trial refund."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    agreement_data = agreement_data_with_trial()

    response = processor.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=agreement_data[0],
        entitlement_id="FENT-2502-5308-4600",
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
        entitlement_termination_date="2025-06-10T08:22:44.126636Z",
    )

    assert isinstance(response[0], Refund)
    assert response[0].description == "Refund due to trial period (from 01 Jun 2025 to 15 Jun 2025)"
    assert response[0].start_date == date(2025, 6, 1)
    assert response[0].end_date == date(2025, 6, 15)


def test_generate_refunds_trial_and_entitlement(
    daily_expenses: dict, agreement_data_with_trial
) -> None:
    """Trials take priority over entitlements when their periods overlap."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    data = agreement_data_with_trial()

    response = processor.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=data[0],
        entitlement_id="FENT-2502-5308-4600",
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
        entitlement_termination_date="2025-06-30T08:22:44.126636Z",
    )

    assert response[0].description == "Refund due to trial period (from 01 Jun 2025 to 15 Jun 2025)"
    assert response[0].start_date == date(2025, 6, 1)
    assert response[0].end_date == date(2025, 6, 15)
    assert response[1].description == "Refund due to active entitlement FENT-2502-5308-4600"
    assert response[1].start_date == date(2025, 6, 16)
    assert response[1].end_date == date(2025, 6, 30)


def test_generate_refunds_entitlement_only(daily_expenses: dict, agreement_data_no_trial) -> None:
    """With only an entitlement active, a single entitlement refund is produced."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    agreement_data = agreement_data_no_trial()

    response = processor.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=agreement_data[0],
        entitlement_id="FENT-2502-5308-4600",
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
    )

    assert response[0].description == "Refund due to active entitlement FENT-2502-5308-4600"
    assert response[0].start_date == date(2025, 6, 1)
    assert response[0].end_date == date(2025, 6, 30)


def test_generate_refunds_no_trial_no_entitlement(
    daily_expenses: dict, agreement_data_no_trial
) -> None:
    """With neither a trial nor an entitlement, no refunds are produced."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    data = agreement_data_no_trial()

    response = processor.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=data[0],
        entitlement_id="FENT-2502-5308-4600",
    )

    assert response == []


def test_generate_refunds_no_entitlement_end_date(
    daily_expenses: dict, agreement_data_with_trial
) -> None:
    """A missing entitlement termination date falls back to the billing end date."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    data = agreement_data_with_trial()

    response = processor.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=data[0],
        entitlement_id="FENT-2502-5308-4600",
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
    )

    assert response[0].description == "Refund due to trial period (from 01 Jun 2025 to 15 Jun 2025)"
    assert response[1].description == "Refund due to active entitlement FENT-2502-5308-4600"
    assert response[1].start_date == date(2025, 6, 16)
    assert response[1].end_date == date(2025, 6, 30)


# ----------------------------------------------------------------------------------
# - get_entitlement_days()
# ----------------------------------------------------------------------------------


def test_get_entitlement_days_with_no_entitlement_end_date() -> None:
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    response = processor.get_entitlement_days(
        trial_days=set(range(1, 21)),
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
    )
    assert response == set(range(21, 31))


def test_get_entitlement_days_with_entitlement_end_date() -> None:
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    response = processor.get_entitlement_days(
        trial_days=set(range(1, 21)),
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
        entitlement_end_date="2025-06-25T08:22:44.126636Z",
    )
    assert response == set(range(21, 26))


# ----------------------------------------------------------------------------------
# - _resolve_datasource_type_name()
# ----------------------------------------------------------------------------------


def test_resolve_datasource_type_name_unknown_logs_and_returns_input(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unknown datasource type is logged and returned unchanged."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)

    with caplog.at_level(logging.WARNING):
        result = processor._resolve_datasource_type_name("unknown_cnr")

    assert result == "unknown_cnr"
    assert "[AUT-5305-9928] Unknown datasource type unknown_cnr" in caplog.text


# ----------------------------------------------------------------------------------
# - maybe_call()
# ----------------------------------------------------------------------------------


async def test_maybe_call_dry_run_true() -> None:
    """In dry-run mode the wrapped function is not called."""
    processor = AuthorizationProcessor(
        year=2025, month=6, authorization=AUTHORIZATION, dry_run=True
    )
    mock_func = AsyncMock(return_value="should not be called")

    result = await processor.maybe_call(mock_func, 1, key="value")

    mock_func.assert_not_awaited()
    assert result is None


async def test_maybe_call_dry_run_false() -> None:
    """Outside dry-run mode the wrapped function is awaited."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    mock_func = AsyncMock(return_value="called")

    result = await processor.maybe_call(mock_func, 1, key="value")

    mock_func.assert_awaited_once_with(1, key="value")
    assert result == "called"


# ----------------------------------------------------------------------------------
# - acquire_semaphore()
# ----------------------------------------------------------------------------------


async def test_acquire_semaphore_acquires_and_releases(mocker: MockerFixture) -> None:
    """The semaphore is acquired on entry and released on exit."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    semaphore = mocker.Mock()
    semaphore.acquire = AsyncMock()
    semaphore.release = mocker.Mock()
    processor.semaphore = semaphore

    async with processor.acquire_semaphore():
        semaphore.acquire.assert_awaited_once()
        semaphore.release.assert_not_called()

    semaphore.release.assert_called_once()


# ----------------------------------------------------------------------------------
# - build_filepath()
# ----------------------------------------------------------------------------------


@pytest.mark.parametrize("dry_run", [True, False])
def test_build_filepath_formats_correctly(dry_run: bool) -> None:
    """The file path depends on dry-run mode."""
    processor = AuthorizationProcessor(
        year=2025, month=6, authorization=AUTHORIZATION, dry_run=dry_run
    )

    result = processor.build_filepath()
    expected_filename = "charges_AUT-5305-9928_2025_06.jsonl"

    if dry_run:
        assert result == expected_filename
    else:
        assert result.endswith(expected_filename)
        assert result.startswith(tempfile.gettempdir())


# ----------------------------------------------------------------------------------
# - _safe_unlink()
# ----------------------------------------------------------------------------------


async def test_safe_unlink_success(mocker: MockerFixture) -> None:
    """A successful unlink removes the file."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    mock_unlink = mocker.patch("aiofiles.os.unlink", new_callable=AsyncMock)

    await processor._safe_unlink("/tmp/valid_file.jsonl")

    mock_unlink.assert_called_once_with("/tmp/valid_file.jsonl")


async def test_safe_unlink_file_not_found(
    mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    """A missing file is logged at debug level and ignored."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    mocker.patch("aiofiles.os.unlink", new_callable=AsyncMock, side_effect=FileNotFoundError())

    with caplog.at_level(logging.DEBUG):
        await processor._safe_unlink("/tmp/nonexistent_file.jsonl")

    assert "File /tmp/nonexistent_file.jsonl not found during cleanup, ignoring" in caplog.text


async def test_safe_unlink_generic_exception(
    mocker: MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    """Any other error is logged at warning level."""
    processor = AuthorizationProcessor(year=2025, month=6, authorization=AUTHORIZATION)
    mocker.patch(
        "aiofiles.os.unlink",
        new_callable=AsyncMock,
        side_effect=PermissionError("Permission denied"),
    )

    with caplog.at_level(logging.WARNING):
        await processor._safe_unlink("/tmp/protected_file.jsonl")

    assert "Failed to cleanup file /tmp/protected_file.jsonl: Permission denied" in caplog.text


# ----------------------------------------------------------------------------------
# - module-level utility functions
# ----------------------------------------------------------------------------------


def test_split_entitlement_days_into_ranges_empty() -> None:
    assert split_entitlement_days_into_ranges(set()) == []


def test_split_entitlement_days_into_ranges_single_day() -> None:
    assert split_entitlement_days_into_ranges({5}) == [(5, 5)]


def test_split_entitlement_days_into_ranges_contiguous() -> None:
    assert split_entitlement_days_into_ranges({1, 2, 3, 4}) == [(1, 4)]


def test_split_entitlement_days_into_ranges_non_contiguous() -> None:
    assert split_entitlement_days_into_ranges({1, 2, 5, 6, 9}) == [(1, 2), (5, 6), (9, 9)]


def test_get_trial_dates_passes_through(mocker: MockerFixture) -> None:
    start = date(2025, 6, 1)
    end = date(2025, 6, 15)
    mocker.patch("app.billing.process_billing.get_trial_start_date", return_value=start)
    mocker.patch("app.billing.process_billing.get_trial_end_date", return_value=end)

    assert get_trial_dates(agreement={"id": "AGR-1"}) == (start, end)


def test_get_billing_percentage_from_agreement() -> None:
    agreement = {
        "parameters": {
            "fulfillment": [{"externalId": "billedPercentage", "value": "7"}],
        }
    }
    assert get_billing_percentage(agreement=agreement) == Decimal("7")


def test_get_billing_percentage_falls_back_to_default(test_settings: Settings) -> None:
    agreement: dict[str, Any] = {"parameters": {"fulfillment": []}}
    assert get_billing_percentage(agreement=agreement) == Decimal(
        test_settings.default_billed_percentage
    )

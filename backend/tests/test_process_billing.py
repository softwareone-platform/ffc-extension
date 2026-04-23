import json
import logging
import tempfile
from _decimal import Decimal
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest
import typer
from app.billing.dataclasses import CurrencyConversionInfo, ProcessResultInfo, Refund
from app.billing.enum import ProcessResult
from app.billing.exceptions import ExchangeRatesClientError, JournalStatusError, JournalSubmitError
from app.billing.notification_helper import check_results
from freezegun import freeze_time

# - test evaluate_journal_status()


@pytest.mark.asyncio()
async def test_evaluate_journal_status_draft(
    existing_journal_file_response, billing_process_instance, caplog
):
    """if a journal exists, it should return it as it is"""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    with caplog.at_level(logging.INFO):
        result = await billing_process_instance.evaluate_journal_status(
            journal_external_id="202505",
        )
        assert result == existing_journal_file_response["data"][0]
    assert (
        "[AUT-5305-9928] Already found journal: BJO-9000-4019 with status Draft"
        in caplog.messages[0]
    )


@pytest.mark.asyncio()
async def test_evaluate_journal_status_validated(
    existing_journal_file_response, billing_process_instance, caplog
):
    """if a journal exists and its status is Validate, it should return the journal as it is"""
    billing_process_instance.mpt_client = AsyncMock()
    existing_journal_file_response["data"][0]["status"] = "Validated"
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    with caplog.at_level(logging.INFO):
        result = await billing_process_instance.evaluate_journal_status(
            journal_external_id="202505",
        )
        assert result == existing_journal_file_response["data"][0]
    assert (
        "[AUT-5305-9928] Already found journal: BJO-9000-4019 with status Validated"
        in caplog.messages[0]
    )


@pytest.mark.asyncio()
async def test_evaluate_journal_different_from_draft_and_not_validated(
    existing_journal_file_response, billing_process_instance, caplog
):
    """if a journal exists and its status is != from Validated or Draft,
    it should raise a JournalStatusError"""
    billing_process_instance.mpt_client = AsyncMock()
    existing_journal_file_response["data"][0]["status"] = "Another Status"
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(JournalStatusError):
            await billing_process_instance.evaluate_journal_status(
                journal_external_id="202505",
            )
    assert (
        "[AUT-5305-9928] Found the journal BJO-9000-4019 with status Another Status"
        in caplog.messages[0]
    )


@pytest.mark.asyncio()
async def test_evaluate_journal_passing_none(billing_process_instance, caplog):
    """if the journal does not exist, it should return None"""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=None
    )
    with caplog.at_level(logging.INFO):
        response = await billing_process_instance.evaluate_journal_status(
            journal_external_id="202505",
        )
        assert response is None
    assert "[AUT-5305-9928] No journal found for external ID: 202505" in caplog.messages[0]


@pytest.mark.asyncio()
async def test_evaluate_journal_with_invalid_status_enum_not_in_valid_list(
    existing_journal_file_response, billing_process_instance, caplog
):
    """Test when journal status is a valid enum but NOT in VALID_JOURNAL_STATUSES list.

    This tests the code path:
        if journal_status_enum in VALID_JOURNAL_STATUSES:
            ...
        else:
            error_msg = f"Found the journal {journal_id} with invalid status
            {journal_status_enum.value}"
            self.logger.error(error_msg)
            raise JournalStatusError(error_msg, journal_id)
    """
    from app.billing.enum import JournalStatus

    billing_process_instance.mpt_client = AsyncMock()
    existing_journal_file_response["data"][0]["status"] = "Review"
    journal_id = existing_journal_file_response["data"][0]["id"]
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )

    filtered_statuses = frozenset(
        [
            JournalStatus.DRAFT,
            JournalStatus.VALIDATED,
        ]
    )

    with patch("app.billing.process_billing.VALID_JOURNAL_STATUSES", filtered_statuses):
        with caplog.at_level(logging.ERROR):
            with pytest.raises(JournalStatusError) as exc_info:
                await billing_process_instance.evaluate_journal_status(
                    journal_external_id="202505",
                )

        assert f"Found the journal {journal_id} with invalid status Review" in caplog.text
        assert exc_info.value.journal_id == journal_id


# ----------------------------------------------------------------------------------
# - Test is_journal_validated
@pytest.mark.asyncio()
async def test_is_journal_validated_success(
    billing_process_instance, existing_journal_file_response, caplog
):
    """if the given journal's status  is VALIDATED, it should return True"""
    billing_process_instance.mpt_client = AsyncMock()
    existing_journal_file_response["data"][0]["status"] = "Validated"
    billing_process_instance.mpt_client.get_journal = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    result = await billing_process_instance.is_journal_status_validated(
        journal_id=existing_journal_file_response["data"][0]["id"]
    )
    assert result is True


@pytest.mark.asyncio()
async def test_is_journal_validated_fail_and_retry(
    mocker, billing_process_instance, existing_journal_file_response, caplog
):
    """if the given journal's status  is not VALIDATED,
    the function should retry for a number of 5 attempts and fails if no response is received"""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.get_journal = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    mocker.patch("asyncio.sleep", return_value=None)  # bypass real function's delay
    result = await billing_process_instance.is_journal_status_validated(
        journal_id=existing_journal_file_response["data"][0]["id"]
    )
    assert result is False
    assert billing_process_instance.mpt_client.get_journal.call_count == 5


@pytest.mark.asyncio()
async def test_is_journal_validated_uses_default_max_attempts(mocker, billing_process_instance):
    """if max_attempts is not provided, default JOURNAL_VALIDATION_MAX_ATTEMPTS is used."""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.get_journal = AsyncMock(return_value={"status": "Draft"})

    mocker.patch("asyncio.sleep", return_value=None)
    mocker.patch.object(billing_process_instance.settings, "journal_validation_max_attempts", 3)
    result = await billing_process_instance.is_journal_status_validated("BJO-9000-4019")

    assert result is False
    assert billing_process_instance.mpt_client.get_journal.call_count == 3


@pytest.mark.asyncio()
async def test_is_journal_validated_logs_warning_on_exception(
    mocker, billing_process_instance, caplog
):
    """exceptions during checks should be logged as warnings and not break the retry loop."""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.get_journal = AsyncMock(
        side_effect=Exception("temporary error")
    )

    mocker.patch("asyncio.sleep", return_value=None)

    with caplog.at_level(logging.WARNING):
        result = await billing_process_instance.is_journal_status_validated(
            "BJO-9000-4019", max_attempts=2
        )

    assert result is False
    assert billing_process_instance.mpt_client.get_journal.call_count == 2
    assert "Error checking journal status on attempt 1: temporary error" in caplog.text


# ----------------------------------------------------------------------------------
# - Test write_charges_file()
@pytest.mark.asyncio()
async def test_write_charges_file_success_no_trial_start_trial_end(
    billing_process_instance,
    patch_get_by_billing_currency,
    patch_get_agreements_from_mpt,
    patch_return_datasource_expenses,
    temp_charges_file,
    caplog,
):
    """if no trial_start and trial_end are provided, the functions still returns True"""
    billing_process_instance.generate_datasource_charges = AsyncMock(
        return_value=['{"id": 1, "name": "test_1"}\n', '{"id": 2, "name": "test_2"}\n']
    )
    result = await billing_process_instance.write_charges_file(
        filepath=temp_charges_file,
    )
    assert result is True


@pytest.mark.asyncio()
async def test_write_charges_file_success(
    billing_process_instance,
    caplog,
    patch_get_agreements_with_trial,
    patch_get_by_billing_currency,
    patch_return_datasource_expenses,
    temp_charges_file,
):
    """the successful case"""
    billing_process_instance.generate_datasource_charges = AsyncMock(
        return_value=['{"id": 1, "name": "test_1"}\n', '{"id": 2, "name": "test_2"}\n']
    )
    result = await billing_process_instance.write_charges_file(
        filepath=temp_charges_file,
    )
    assert result is True


@pytest.mark.asyncio()
async def test_write_charges_file_empty_file(
    billing_process_instance,
    patch_get_by_billing_currency,
    patch_get_agreements_from_mpt,
    patch_return_datasource_expenses,
    temp_charges_file,
    caplog,
):
    """if an empty file is provided, it should return False, no files were written"""
    billing_process_instance.generate_datasource_charges = AsyncMock(return_value={})
    result = await billing_process_instance.write_charges_file(
        filepath=temp_charges_file,
    )
    assert result is False


@pytest.mark.asyncio()
async def test_write_charges_file_agr_000(
    billing_process_instance,
    patch_get_by_billing_currency_for_agr_000,
    patch_return_datasource_expenses,
    patch_get_agreements_from_mpt,
    temp_charges_file,
    caplog,
):
    """if an agr_000 is provided, it should return False because no files will be written"""
    with caplog.at_level(logging.INFO):
        billing_process_instance.generate_datasource_charges = AsyncMock(
            return_value=['{"id": 1, "name": "test_1"}\n', '{"id": 2, "name": "test_2"}\n']
        )
        result = await billing_process_instance.write_charges_file(
            filepath=temp_charges_file,
        )
        assert (
            "[AUT-5305-9928] Skip organization FORG-4801-6958-2949 - "
            "SoftwareOne (Test Environment) because of ID AGR-0000-0000-0000" in caplog.messages[1]
        )
        assert result is False


@pytest.mark.asyncio()
async def test_write_charges_file_many_agreements(
    mocker,
    billing_process_instance,
    patch_get_by_billing_currency,
    agreements,
    patch_return_datasource_expenses,
    temp_charges_file,
    caplog,
):
    """if many agreements are provided for a given org,
    they will be skipped and no file will be written"""
    agreements["data"][0]["authorization"]["id"] = "AUT-5305-9928"
    agreements["data"].append(agreements["data"][0])

    async def agr_mock_generator():
        for agr in agreements["data"]:
            yield agr

    with caplog.at_level(logging.INFO):
        mocker.patch.object(
            billing_process_instance.mpt_client,
            "get_agreements_by_organization",
            return_value=agr_mock_generator(),
        )

    with caplog.at_level(logging.INFO):
        billing_process_instance.generate_datasource_charges = AsyncMock(
            return_value=['{"id": 1, "name": "test_1"}\n', '{"id": 2, "name": "test_2"}\n']
        )
        result = await billing_process_instance.write_charges_file(
            filepath=temp_charges_file,
        )
        assert (
            "[AUT-5305-9928] Found 2 while we were expecting "
            "1 for the organization FORG-4801-6958-2949" in caplog.messages[1]
        )
        assert result is False


@pytest.mark.asyncio()
async def test_write_charges_file_different_auth_id(
    mocker,
    billing_process_instance,
    patch_get_by_billing_currency,
    agreements,
    patch_return_datasource_expenses,
    temp_charges_file,
    caplog,
):
    """if the authorization's ID of a given agreement is different from the one defined, those
    agreements will be skipped and no file will be written"""
    agreements["data"][0]["authorization"]["id"] = "AUT-5305-9955"

    async def agr_mock_generator():
        for agr in agreements["data"]:
            yield agr

    with caplog.at_level(logging.INFO):
        mocker.patch.object(
            billing_process_instance.mpt_client,
            "get_agreements_by_organization",
            return_value=agr_mock_generator(),
        )
        billing_process_instance.generate_datasource_charges = AsyncMock(
            return_value=['{"id": 1, "name": "test_1"}\n', '{"id": 2, "name": "test_2"}\n']
        )
        result = await billing_process_instance.write_charges_file(
            filepath=temp_charges_file,
        )
        assert (
            "[AUT-5305-9928] Skipping organization "
            "FORG-4801-6958-2949 because it belongs "
            "to an agreement with different authorization: AUT-5305-9955" in caplog.messages[1]
        )
        assert result is False


# ----------------------------------------------------------------------------------
# - Test attach_exchange_rates()


@pytest.mark.asyncio()
async def test_attach_exchange_rates_with_existing_attachment(
    billing_process_instance, journal_attachment_response, create_journal_response, exchange_rates
):
    """if a journal already has an attachment, it will be deleted and a new one will be attached."""
    billing_process_instance.mpt_client = AsyncMock()

    billing_process_instance.mpt_client.fetch_journal_attachment = AsyncMock(
        return_value=journal_attachment_response["data"][0]
    )
    billing_process_instance.mpt_client.delete_journal_attachment = AsyncMock(return_value={})
    billing_process_instance.mpt_client.create_journal_attachment = AsyncMock(
        return_value=journal_attachment_response
    )

    result = await billing_process_instance.attach_exchange_rates(
        journal_id="BJO-9000-4019", currency="EUR", exchange_rates=exchange_rates
    )
    assert result == journal_attachment_response


@pytest.mark.asyncio()
async def test_attach_exchange_rates_with_no_existing_attachment(
    billing_process_instance, journal_attachment_response, create_journal_response, exchange_rates
):
    """if a journal has no attachment, it will be created and attached."""
    billing_process_instance.mpt_client = AsyncMock()

    billing_process_instance.mpt_client.fetch_journal_attachment = AsyncMock(return_value=[])
    billing_process_instance.mpt_client.create_journal_attachment = AsyncMock(
        return_value=journal_attachment_response
    )

    result = await billing_process_instance.attach_exchange_rates(
        journal_id="BJO-9000-4019", currency="EUR", exchange_rates=exchange_rates
    )
    assert result == journal_attachment_response


# -------------------------------------------------------------------------------------
# - Test complete_journal_process()
@pytest.mark.asyncio()
async def test_complete_journal_process_success(
    billing_process_instance,
    create_journal_response,
    journal_attachment_response,
    temp_charges_file,
    caplog,
    exchange_rates,
):
    """if a Journal is created successfully, the exchanges_rate_json will be attached and if the
    status of the journal is Validated, the journal will be submitted. None is returned"""
    create_journal_response["status"] = "Validated"
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.create_journal = AsyncMock(
        return_value=create_journal_response
    )
    billing_process_instance.mpt_client.get_journal = AsyncMock(
        return_value=create_journal_response
    )
    billing_process_instance.mpt_client.upload_charges = AsyncMock(return_value=None)
    billing_process_instance.mpt_client.submit_journal = AsyncMock(return_value=True)
    billing_process_instance.exchange_rates = exchange_rates
    billing_process_instance.mpt_client.attach_exchange_rates = AsyncMock(return_value=None)
    expected_respone = {
        "$meta": {"omitted": ["processing"]},
        "audit": {
            "created": {
                "at": "2025-06-10T17:04:53.802Z",
                "by": {"icon": "", "id": "TKN-5645-5497", "name": "Antonio Di Mariano"},
            },
            "updated": {},
        },
        "authorization": {"currency": "USD", "id": "AUT-5305-9928", "name": "asdasdsa"},
        "dueDate": "2025-07-01T00:00:00.000Z",
        "externalIds": {"vendor": "202506"},
        "id": "BJO-9000-4019",
        "name": "June 2025 Charges",
        "owner": {
            "externalId": "US",
            "icon": "/v1/accounts/sellers/SEL-7032-1456/icon",
            "id": "SEL-7032-1456",
            "name": "SoftwareONE Inc.",
        },
        "price": {"currency": "USD", "totalPP": 0.0},
        "product": {
            "externalIds": {"operations": "adsasadsa"},
            "icon": "/v1/catalog/products/PRD-2426-7318/icon",
            "id": "PRD-2426-7318",
            "name": "FinOps for Cloud",
            "status": "Published",
        },
        "status": "Validated",
        "upload": {"error": 0, "ready": 0, "split": 0, "total": 0},
        "vendor": {
            "icon": "/v1/accounts/accounts/ACC-3102-8586/icon",
            "id": "ACC-3102-8586",
            "name": "FinOps for Cloud",
            "status": "Active",
            "type": "Vendor",
        },
    }
    with caplog.at_level(logging.INFO):
        response = await billing_process_instance.complete_journal_process(
            filepath=temp_charges_file,
            journal=None,
            journal_external_id="BJO-9000-4019",
        )
        assert response == expected_respone
    assert "[AUT-5305-9928] new journal created: BJO-9000-4019" in caplog.messages[0]
    assert "[AUT-5305-9928] submitting the journal BJO-9000-4019." in caplog.messages[1]


@pytest.mark.asyncio()
async def test_complete_journal_process_fail(
    billing_process_instance,
    create_journal_response,
    journal_attachment_response,
    exchange_rates,
    temp_charges_file,
    caplog,
):
    """if a Journal is created successfully,
    the exchanges_rate_json will be attached. If the journal's status
    is not validated, it won't be submitted. JournalSubmitError will be raised."""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.create_journal = AsyncMock(
        return_value=create_journal_response
    )
    billing_process_instance.mpt_client.get_journal_by_id = AsyncMock()
    billing_process_instance.mpt_client.upload_charges = AsyncMock(return_value=None)
    billing_process_instance.is_journal_status_validated = AsyncMock(return_value=False)
    billing_process_instance.mpt_client.submit_journal = AsyncMock(return_value=True)
    billing_process_instance.mpt_client.attach_exchange_rates = AsyncMock(return_value=None)
    billing_process_instance.mpt_client.is_journal_validated = AsyncMock(return_value=True)
    billing_process_instance.exchange_rates = exchange_rates
    billing_process_instance.attach_exchange_rates = AsyncMock(
        return_value=journal_attachment_response
    )

    with caplog.at_level(logging.INFO):
        with pytest.raises(JournalSubmitError):
            await billing_process_instance.complete_journal_process(
                filepath=temp_charges_file,
                journal=create_journal_response,
                journal_external_id="BJO-9000-4019",
            )

    assert (
        "[AUT-5305-9928] cannot submit the journal BJO-9000-4019 it doesn't get validated"
        in caplog.messages[0]
    )


# ------------------------------------------------------------------------
# - Test generate_datasource_charges()


@pytest.mark.asyncio()
async def test_generate_datasource_charges_empty_daily_expenses(
    billing_process_instance, build_test_organization, agreement_data_no_trial
):
    """if no daily_expenses are provided, there will be no charges for the given datasource"""
    agreement_data = agreement_data_no_trial()
    response = await billing_process_instance.generate_datasource_charges(
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
    assert line.get("description").get("value2") == "No charges available for this datasource."


@pytest.mark.parametrize("billing_process_instance", [{"month": 9}], indirect=True)
@pytest.mark.asyncio()
async def test_generate_datasource_charges_with_daily_expenses_active_trial_terminated_entitlements(
    billing_process_instance,
    build_test_organization,
    agreement_data_with_trial,
    daily_expenses,
    exchange_rates,
    patch_get_for_billing,
    active_entitlement,
    caplog,
):
    active_entitlement["events"]["terminated"] = {
        "at": "2025-09-28T07:47:19.142190Z",
        "by": {"id": "FTKN-4573-9711", "type": "system", "name": "Microsoft CSP Extension"},
    }

    billing_process_instance.exchange_rate_client = AsyncMock()

    billing_process_instance.exchange_rate_client.fetch_exchange_rates = AsyncMock(
        return_value=exchange_rates
    )
    agreement_data_with_trial = agreement_data_with_trial(
        parameters={
            "fulfillment": [
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
                    "id": "PAR-7208-0459-0009",
                    "externalId": "trialStartDate",
                    "name": "Trial period start date",
                    "type": "Date",
                    "phase": "Fulfillment",
                    "displayValue": "2025-08-27",
                    "value": "2025-08-27",
                },
                {
                    "id": "PAR-7208-0459-0010",
                    "externalId": "trialEndDate",
                    "name": "Trial period end date",
                    "type": "Date",
                    "phase": "Fulfillment",
                    "displayValue": "2025-09-15",
                    "value": "2025-09-15",
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
        }
    )
    with caplog.at_level(logging.INFO):
        response = await billing_process_instance.generate_datasource_charges(
            organization=build_test_organization,
            agreement=agreement_data_with_trial[0],
            linked_datasource_id="34654563456",
            linked_datasource_type="aws_cnr",
            datasource_id="34654563488",
            datasource_name="Test",
            daily_expenses=daily_expenses,
        )
        assert isinstance(response[0], str)
        lines = [json.loads(r) for r in response]
        assert lines[0] == {
            "externalIds": {"vendor": "34654563456-01", "invoice": "-", "reference": "34654563488"},
            "search": {
                "source": {
                    "type": "Subscription",
                    "criteria": "externalIds.vendor",
                    "value": "FORG-4801-6958-2949",
                },
                "item": {"criteria": "item.externalIds.vendor", "value": "FIN-0001-P1M"},
            },
            "period": {"start": "2025-09-01T00:00:00+00:00", "end": "2025-09-30T23:59:59+00:00"},
            "price": {"unitPP": "183.9829", "PPx1": "183.9829"},
            "quantity": 1,
            "description": {
                "value1": "Amazon Web Services datasource with name Test and id 34654563488",
                "value2": "",
            },
            "segment": "COM",
        }
        assert lines[1] == {
            "externalIds": {"vendor": "34654563456-02", "invoice": "-", "reference": "34654563488"},
            "search": {
                "source": {
                    "type": "Subscription",
                    "criteria": "externalIds.vendor",
                    "value": "FORG-4801-6958-2949",
                },
                "item": {"criteria": "item.externalIds.vendor", "value": "FIN-0001-P1M"},
            },
            "period": {"start": "2025-09-01T00:00:00+00:00", "end": "2025-09-15T23:59:59+00:00"},
            "price": {"unitPP": "-39.1447", "PPx1": "-39.1447"},
            "quantity": 1,
            "description": {
                "value1": "Amazon Web Services datasource with name Test and id 34654563488",
                "value2": "Refund due to trial period (from 27 Aug 2025 to 15 Sep 2025)",
            },
            "segment": "COM",
        }
        assert lines[2] == {
            "externalIds": {"vendor": "34654563456-03", "invoice": "-", "reference": "34654563488"},
            "search": {
                "source": {
                    "type": "Subscription",
                    "criteria": "externalIds.vendor",
                    "value": "FORG-4801-6958-2949",
                },
                "item": {"criteria": "item.externalIds.vendor", "value": "FIN-0001-P1M"},
            },
            "period": {"start": "2025-09-16T00:00:00+00:00", "end": "2025-09-28T23:59:59+00:00"},
            "price": {"unitPP": "-137.9294", "PPx1": "-137.9294"},
            "quantity": 1,
            "description": {
                "value1": "Amazon Web Services datasource with name Test and id 34654563488",
                "value2": "Refund due to active entitlement FENT-9763-4488-4624",
            },
            "segment": "COM",
        }
        assert (
            "[AUT-5305-9928] : organization_id='FORG-4801-6958-2949'"
            " linked_datasource_id='34654563456' datasource_name='Test' - "
            "amount=Decimal('5326.0458') billing_percentage=Decimal('4') "
            "price_in_source_currency=Decimal('213.0418') "
            "exchange_rate=Decimal('0.8636') price_in_target_currency=Decimal('183.98289848')"
            in caplog.messages[0]
        )


@pytest.mark.parametrize("billing_process_instance", [{"month": 9}], indirect=True)
@pytest.mark.asyncio()
async def test_generate_datasource_charges_with_daily_expenses_active_trial_and_active_entitlements(
    billing_process_instance,
    agreement_data_with_trial,
    daily_expenses,
    exchange_rates,
    patch_get_for_billing,
    active_entitlement,
    build_test_organization,
    caplog,
):
    """if there are daily_expenses, charges will be generated for the given datasource"""
    billing_process_instance.exchange_rate_client = AsyncMock()

    billing_process_instance.exchange_rate_client.fetch_exchange_rates = AsyncMock(
        return_value=exchange_rates
    )
    agreement_data_with_trial = agreement_data_with_trial(
        parameters={
            "fulfillment": [
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
                    "id": "PAR-7208-0459-0009",
                    "externalId": "trialStartDate",
                    "name": "Trial period start date",
                    "type": "Date",
                    "phase": "Fulfillment",
                    "displayValue": "2025-08-27",
                    "value": "2025-08-27",
                },
                {
                    "id": "PAR-7208-0459-0010",
                    "externalId": "trialEndDate",
                    "name": "Trial period end date",
                    "type": "Date",
                    "phase": "Fulfillment",
                    "displayValue": "2025-09-26",
                    "value": "2025-09-26",
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
        }
    )

    with caplog.at_level(logging.INFO):
        response = await billing_process_instance.generate_datasource_charges(
            organization=build_test_organization,
            agreement=agreement_data_with_trial[0],
            linked_datasource_id="34654563456",
            linked_datasource_type="aws_cnr",
            datasource_id="34654563488",
            datasource_name="Test",
            daily_expenses=daily_expenses,
        )
        assert isinstance(response[0], str)
        lines = [json.loads(r) for r in response]
        assert lines[0] == {
            "externalIds": {"vendor": "34654563456-01", "invoice": "-", "reference": "34654563488"},
            "search": {
                "source": {
                    "type": "Subscription",
                    "criteria": "externalIds.vendor",
                    "value": "FORG-4801-6958-2949",
                },
                "item": {"criteria": "item.externalIds.vendor", "value": "FIN-0001-P1M"},
            },
            "period": {"start": "2025-09-01T00:00:00+00:00", "end": "2025-09-30T23:59:59+00:00"},
            "price": {"unitPP": "183.9829", "PPx1": "183.9829"},
            "quantity": 1,
            "description": {
                "value1": "Amazon Web Services datasource with name Test and id 34654563488",
                "value2": "",
            },
            "segment": "COM",
        }
        assert lines[1] == {
            "externalIds": {"vendor": "34654563456-02", "invoice": "-", "reference": "34654563488"},
            "search": {
                "source": {
                    "type": "Subscription",
                    "criteria": "externalIds.vendor",
                    "value": "FORG-4801-6958-2949",
                },
                "item": {"criteria": "item.externalIds.vendor", "value": "FIN-0001-P1M"},
            },
            "period": {"start": "2025-09-01T00:00:00+00:00", "end": "2025-09-26T23:59:59+00:00"},
            "price": {"unitPP": "-153.1250", "PPx1": "-153.1250"},
            "quantity": 1,
            "description": {
                "value1": "Amazon Web Services datasource with name Test and id 34654563488",
                "value2": "Refund due to trial period (from 27 Aug 2025 to 26 Sep 2025)",
            },
            "segment": "COM",
        }
        assert (
            "[AUT-5305-9928] : organization_id='FORG-4801-6958-2949' "
            "linked_datasource_id='34654563456' datasource_name='Test' - "
            "amount=Decimal('5326.0458') billing_percentage=Decimal('4') "
            "price_in_source_currency=Decimal('213.0418') "
            "exchange_rate=Decimal('0.8636') price_in_target_currency=Decimal('183.98289848')"
            in caplog.messages[0]
        )


@pytest.mark.asyncio()
async def test_generate_datasource_charges_stores_exchange_rates_by_base_currency(
    billing_process_instance, build_test_organization
):
    """when conversion info includes exchange_rates, they are cached by base currency."""
    billing_process_instance.generate_refund_lines = AsyncMock(return_value=[])
    billing_process_instance.get_currency_conversion_info = AsyncMock(
        return_value=CurrencyConversionInfo(
            base_currency="USD",
            billing_currency="EUR",
            exchange_rate=Decimal("1.1000"),
            exchange_rates={"conversion_rates": {"EUR": 1.1}},
        )
    )

    agreement = {
        "parameters": {
            "fulfillment": [
                {
                    "externalId": "billedPercentage",
                    "value": "4",
                }
            ]
        }
    }

    await billing_process_instance.generate_datasource_charges(
        organization=build_test_organization,
        agreement=agreement,
        linked_datasource_id="34654563456",
        linked_datasource_type="aws_cnr",
        datasource_id="ds-1",
        datasource_name="DS One",
        daily_expenses={1: Decimal("100")},
    )

    assert billing_process_instance.exchange_rates["USD"] == {"conversion_rates": {"EUR": 1.1}}


@pytest.mark.asyncio()
async def test_generate_datasource_charges_with_price_in_source_currency_eq_0(
    billing_process_instance,
    daily_expenses,
    exchange_rates,
    patch_get_for_billing,
    agreement_data_with_trial,
    build_test_organization,
    caplog,
):
    """if there are daily_expenses, but no charges, a line will be added to
    the monthly charge file with 0"""
    billing_process_instance.exchange_rate_client = AsyncMock()
    billing_process_instance.exchange_rate_client.fetch_exchange_rates = AsyncMock(
        return_value=exchange_rates
    )
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

    with caplog.at_level(logging.INFO):
        response = await billing_process_instance.generate_datasource_charges(
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
    assert line == {
        "externalIds": {"vendor": "34654563456-01", "invoice": "-", "reference": "34654563488"},
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
            "value1": "Amazon Web Services datasource with name Test and id 34654563488",
            "value2": "",
        },
        "segment": "COM",
    }
    assert line.get("price").get("unitPP") == "0.0000"


@pytest.mark.asyncio()
async def test_generate_datasource_charges_with_no_entitlement(
    billing_process_instance,
    agreement_data_with_trial,
    daily_expenses,
    patch_get_for_billing,
    exchange_rates,
    caplog,
    build_test_organization,
):
    """if there are no entitlements, the function still writes the existing charges for the
    given datasource"""
    billing_process_instance.exchange_rate_client = AsyncMock()
    billing_process_instance.exchange_rate_client.fetch_exchange_rates = AsyncMock(
        return_value=exchange_rates
    )
    agreement_data = agreement_data_with_trial()

    with caplog.at_level(logging.INFO):
        response = await billing_process_instance.generate_datasource_charges(
            organization=build_test_organization,
            agreement=agreement_data[0],
            linked_datasource_id="34654563456",
            linked_datasource_type="aws_cnr",
            datasource_id="34654563488",
            datasource_name="Test",
            daily_expenses=daily_expenses,
        )
    assert isinstance(response[0], str)
    lines = [json.loads(r) for r in response]
    assert lines[0] == {
        "externalIds": {"vendor": "34654563456-01", "invoice": "-", "reference": "34654563488"},
        "search": {
            "source": {
                "type": "Subscription",
                "criteria": "externalIds.vendor",
                "value": "FORG-4801-6958-2949",
            },
            "item": {"criteria": "item.externalIds.vendor", "value": "FIN-0001-P1M"},
        },
        "period": {"start": "2025-06-01T00:00:00+00:00", "end": "2025-06-30T23:59:59+00:00"},
        "price": {"unitPP": "183.9829", "PPx1": "183.9829"},
        "quantity": 1,
        "description": {
            "value1": "Amazon Web Services datasource with name Test and id 34654563488",
            "value2": "",
        },
        "segment": "COM",
    }
    assert lines[1] == {
        "externalIds": {"vendor": "34654563456-02", "invoice": "-", "reference": "34654563488"},
        "search": {
            "source": {
                "type": "Subscription",
                "criteria": "externalIds.vendor",
                "value": "FORG-4801-6958-2949",
            },
            "item": {"criteria": "item.externalIds.vendor", "value": "FIN-0001-P1M"},
        },
        "period": {"start": "2025-06-01T00:00:00+00:00", "end": "2025-06-15T23:59:59+00:00"},
        "price": {"unitPP": "-39.1447", "PPx1": "-39.1447"},
        "quantity": 1,
        "description": {
            "value1": "Amazon Web Services datasource with name Test and id 34654563488",
            "value2": "Refund due to trial period (from 01 Jun 2025 to 15 Jun 2025)",
        },
        "segment": "COM",
    }


# ------------------------------------------------------------------------------------
# Test


@pytest.mark.asyncio()
async def test_get_currency_conversion_info_raises_key_error_for_missing_org_fields(
    billing_process_instance, caplog
):
    """missing required organization keys should be logged and re-raised as AttributeError."""
    invalid_organization = SimpleNamespace(
        id="FORG-1234",
        name="Test Org",
        operations_external_id="AGR-1234-5678-9012",
        currency="USD",
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(AttributeError):
            await billing_process_instance.get_currency_conversion_info(
                organization=invalid_organization,
            )

    assert "Missing required attribute in organization" in caplog.text


@pytest.mark.asyncio()
async def test_get_currency_conversion_info_needed(
    billing_process_instance,
    build_test_organization,
    exchange_rates,
    caplog,
    currency_conversion,
):
    """if the billing currency is different from the base currency, the function
    will fetch the exchange rates for the conversion"""
    billing_process_instance.exchange_rate_client = AsyncMock()
    billing_process_instance.exchange_rate_client.fetch_exchange_rates = AsyncMock(
        return_value=exchange_rates
    )
    with caplog.at_level(logging.INFO):
        result = await billing_process_instance.get_currency_conversion_info(
            organization=build_test_organization,
        )
        assert isinstance(result, CurrencyConversionInfo)
        assert result.__dict__ == currency_conversion


@pytest.mark.asyncio()
async def test_get_currency_conversion_info_no_needed(
    billing_process_instance, build_test_organization, exchange_rates, caplog
):
    """if the billing currency is the same as the base currency, no conversion is needed."""
    build_test_organization.billing_currency = "USD"

    billing_process_instance.exchange_rate_client = AsyncMock()
    billing_process_instance.exchange_rate_client.fetch_exchange_rates = AsyncMock(
        return_value=exchange_rates
    )
    with caplog.at_level(logging.INFO):
        result = await billing_process_instance.get_currency_conversion_info(
            organization=build_test_organization,
        )
        assert isinstance(result, CurrencyConversionInfo)
    assert (
        "[AUT-5305-9928] organization FORG-4801-6958-2949 - SoftwareOne (Test Environment) "
        "doesn't need currency conversion" in caplog.messages[0]
    )


@pytest.mark.asyncio()
async def test_check_if_rate_conversion_client_error(
    billing_process_instance, build_test_organization, caplog
):
    """if an error occurs fetching the conversion info, an error message will be printed."""
    build_test_organization.billing_currency = "EUR"
    billing_process_instance.exchange_rate_client.fetch_exchange_rates = AsyncMock(return_value={})

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ExchangeRatesClientError):
            await billing_process_instance.get_currency_conversion_info(
                organization=build_test_organization
            )
    assert (
        "[AUT-5305-9928] An error occurred while fetching exchange rates for USD"
        in caplog.messages[0]
    )


@pytest.mark.asyncio()
async def test_check_if_rate_conversion_response_key_error(
    billing_process_instance, build_test_organization, exchange_rates, caplog
):
    """if an error occurs fetching the conversion info, an error message will be printed."""
    build_test_organization.billing_currency = "EUR"
    billing_process_instance.exchange_rate_client.fetch_exchange_rates = AsyncMock(
        return_value=exchange_rates
    )
    exchange_rates.pop("conversion_rates")

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ExchangeRatesClientError):
            await billing_process_instance.get_currency_conversion_info(
                organization=build_test_organization
            )
    assert "Invalid exchange rates response structure for" in caplog.text


# -----------------------------------------------------------------------------------
# - Test generate_refunds()
def test_generate_refunds_success(
    daily_expenses, billing_process_instance, agreement_data_with_trial
):
    """if there are a  trial and an entitlements active, a refund will be generated.
    Trials get priority over entitlements if the periods overlap."""
    agreement_data = agreement_data_with_trial()
    response = billing_process_instance.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=agreement_data[0],
        entitlement_id="FENT-2502-5308-4600",
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
        entitlement_termination_date="2025-06-10T08:22:44.126636Z",
    )
    assert isinstance(response, list)
    assert isinstance(response[0], Refund)
    assert response[0].description == "Refund due to trial period (from 01 Jun 2025 to 15 Jun 2025)"
    assert response[0].start_date == date(2025, 6, 1)
    assert response[0].end_date == date(2025, 6, 15)


def test_generate_refunds_success_trial_and_entitlements(
    daily_expenses, billing_process_instance, agreement_data_with_trial
):
    """if there are a  trial and an entitlements active, a refund will be generated.
    Trials get priority over entitlements if the periods overlap."""
    data = agreement_data_with_trial()
    response = billing_process_instance.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=data[0],
        entitlement_id="FENT-2502-5308-4600",
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
        entitlement_termination_date="2025-06-30T08:22:44.126636Z",
    )
    assert isinstance(response, list)
    assert isinstance(response[0], Refund)
    assert response[0].description == "Refund due to trial period (from 01 Jun 2025 to 15 Jun 2025)"
    assert response[0].start_date == date(2025, 6, 1)
    assert response[0].end_date == date(2025, 6, 15)
    assert response[1].description == "Refund due to active entitlement FENT-2502-5308-4600"
    assert response[1].start_date == date(2025, 6, 16)
    assert response[1].end_date == date(2025, 6, 30)


def test_generate_refunds_no_trial_days_active_entitlement(
    daily_expenses, billing_process_instance, agreement_data_no_trial
):
    """if only an entitlement is active, there will be a refund for that period."""
    agreement_data = agreement_data_no_trial()
    response = billing_process_instance.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=agreement_data[0],
        entitlement_id="FENT-2502-5308-4600",
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
    )
    assert isinstance(response, list)
    assert isinstance(response[0], Refund)
    assert response[0].description == "Refund due to active entitlement FENT-2502-5308-4600"
    assert response[0].start_date == date(2025, 6, 1)
    assert response[0].end_date == date(2025, 6, 30)


def test_generate_refunds_no_trial_days_no_entitlement_days(
    daily_expenses, billing_process_instance, agreement_data_no_trial
):
    """if there are no trials and no entitlements active, there will be no refund."""
    data = agreement_data_no_trial()
    response = billing_process_instance.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=data[0],
        entitlement_id="FENT-2502-5308-4600",
    )
    assert isinstance(response, list)
    assert len(response) == 0


def test_generate_refunds_no_entitlement_end_date(
    daily_expenses, billing_process_instance, agreement_data_with_trial
):
    """if there is only a trial period and the entitlement_termination_date is missing,
    the billing date will be used as value for calculating the refund. The Trials get priority over
    entitlements."""
    data = agreement_data_with_trial()
    response = billing_process_instance.generate_refunds(
        daily_expenses=daily_expenses,
        agreement=data[0],
        entitlement_id="FENT-2502-5308-4600",
        entitlement_start_date="2025-06-01T08:22:44.126636Z",
    )
    assert isinstance(response, list)
    assert isinstance(response[0], Refund)
    assert response[0].description == "Refund due to trial period (from 01 Jun 2025 to 15 Jun 2025)"
    assert response[0].start_date == date(2025, 6, 1)
    assert response[0].end_date == date(2025, 6, 15)
    assert response[1].description == "Refund due to active entitlement FENT-2502-5308-4600"
    assert response[1].start_date == date(2025, 6, 16)
    assert response[1].end_date == date(2025, 6, 30)


# ----------------------------------------------------------------------
# - Test get_entitlement_days()
def test_get_entitlement_days_with_no_entitlement_end_date(billing_process_instance):
    trial_days = set(range(1, 21))
    entitlement_start_date = "2025-06-01T08:22:44.126636Z"
    response = billing_process_instance.get_entitlement_days(
        trial_days=trial_days, entitlement_start_date=entitlement_start_date
    )
    assert isinstance(response, set)
    assert response == set(range(21, 31))


def test_get_entitlement_days_with_entitlement_end_date(billing_process_instance):
    trial_days = set(range(1, 21))
    entitlement_start_date = "2025-06-01T08:22:44.126636Z"
    entitlement_end_date = "2025-06-25T08:22:44.126636Z"

    response = billing_process_instance.get_entitlement_days(
        trial_days=trial_days,
        entitlement_start_date=entitlement_start_date,
        entitlement_end_date=entitlement_end_date,
    )
    assert isinstance(response, set)
    assert response == set(range(21, 26))


# - Test process()
@pytest.mark.asyncio()
async def test_process_no_count_active_agreements(billing_process_instance, caplog):
    """if an error occur getting the total number of active agreements,
    an error message will be logged.
    and the error will be added to the list of errors"""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements = AsyncMock(return_value=0)
    with caplog.at_level(logging.INFO):
        response = await billing_process_instance.process()
        assert isinstance(response, ProcessResultInfo)
        assert response.authorization_id == "AUT-5305-9928"
        assert response.message == "No active agreement for authorization AUT-5305-9928"


@pytest.mark.asyncio()
async def test_process_success(billing_process_instance, existing_journal_file_response):
    """if the process completed successfully, all the function are called once."""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements = AsyncMock(return_value=2)
    billing_process_instance.write_charges_file = AsyncMock(return_value=True)
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    billing_process_instance.complete_journal_process = AsyncMock(return_value=None)
    await billing_process_instance.process()
    assert billing_process_instance.complete_journal_process.call_count == 1
    assert (
        billing_process_instance.mpt_client.get_journal_by_authorization_external_id.call_count == 1
    )
    assert billing_process_instance.mpt_client.count_active_agreements.call_count == 1
    assert billing_process_instance.write_charges_file.call_count == 1


@pytest.mark.asyncio()
async def test_process_journal_validated(billing_process_instance, existing_journal_file_response):
    """if the process completed successfully, all the function are called once."""
    existing_journal_file_response["data"][0]["status"] = "Validated"
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements = AsyncMock(return_value=2)
    billing_process_instance.write_charges_file = AsyncMock(return_value=True)
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    billing_process_instance.complete_journal_process = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    response = await billing_process_instance.process()
    assert response.result == ProcessResult.JOURNAL_GENERATED
    assert response.message is None
    assert response.journal_id == "BJO-9000-4019"


@pytest.mark.asyncio()
async def test_process_journal_different_from_draft(
    billing_process_instance, existing_journal_file_response
):
    """if the journal status is not VALIDATED or DRAFT, the flow will be stopped."""
    existing_journal_file_response["data"][0]["status"] = "Review"
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements = AsyncMock(return_value=2)
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    response = await billing_process_instance.process()
    assert response.result == ProcessResult.JOURNAL_SKIPPED
    assert response.journal_id == "BJO-9000-4019"


@pytest.mark.asyncio()
async def test_process_no_charges_written(billing_process_instance, existing_journal_file_response):
    """if no charges files are written, the complete_journal_process won't be called."""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements = AsyncMock(return_value=2)
    billing_process_instance.write_charges_file = AsyncMock(return_value=False)
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    billing_process_instance.complete_journal_process = AsyncMock(return_value=None)
    await billing_process_instance.process()
    assert billing_process_instance.complete_journal_process.call_count == 0
    assert (
        billing_process_instance.mpt_client.get_journal_by_authorization_external_id.call_count == 1
    )
    assert billing_process_instance.mpt_client.count_active_agreements.call_count == 1
    assert billing_process_instance.write_charges_file.call_count == 1


@pytest.mark.asyncio()
async def test_process_failure_http_status_error(billing_process_instance, caplog):
    """if an Exception occurs, an ERROR message will be logger"""
    billing_process_instance.mpt_client = AsyncMock()
    mock_json = {"error": "Invalid request"}
    mock_content = b'{"error": "Invalid request"}'
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.content = mock_content
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = mock_json
    mock_request = MagicMock()
    error = httpx.HTTPStatusError("Bad Request", request=mock_request, response=mock_response)

    billing_process_instance.mpt_client.count_active_agreements.side_effect = error
    with caplog.at_level(logging.ERROR):
        await billing_process_instance.process()
    assert "[AUT-5305-9928] 400 " in caplog.messages[0]


@pytest.mark.asyncio()
async def test_process_failure_http_status_error_no_json(billing_process_instance, caplog):
    """if an Exception occurs, an ERROR message will be logger"""
    billing_process_instance.mpt_client = AsyncMock()
    mock_content = b'{"error": "Invalid request"}'
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.content = mock_content
    mock_response.headers = {"Content-Type": "application/text"}
    mock_request = MagicMock()
    error = httpx.HTTPStatusError("Bad Request", request=mock_request, response=mock_response)

    billing_process_instance.mpt_client.count_active_agreements.side_effect = error
    with caplog.at_level(logging.ERROR):
        await billing_process_instance.process()
    assert "[AUT-5305-9928] 400 " in caplog.messages[0]


@pytest.mark.asyncio()
async def test_process_exception(billing_process_instance, caplog):
    """if an Exception occurs, an ERROR message will be logger"""
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements.side_effect = Exception(
        "No good Reasons"
    )
    with caplog.at_level(logging.ERROR):
        await billing_process_instance.process()
    assert "[AUT-5305-9928] An error occurred: No good Reasons" in caplog.messages[0]


@pytest.mark.asyncio()
async def test_process_exception_journal_status_error(billing_process_instance, caplog):
    billing_process_instance.evaluate_journal_status = AsyncMock(
        side_effect=JournalStatusError("an error occurred.", journal_id="BJO-9000-4019")
    )
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements = AsyncMock(return_value=2)
    billing_process_instance.write_charges_file = AsyncMock(return_value=True)

    response = await billing_process_instance.process()
    assert response.result is ProcessResult.JOURNAL_SKIPPED
    assert response.journal_id == "BJO-9000-4019"
    assert response.message == "an error occurred."


@pytest.mark.asyncio()
async def test_process_exception_journal_submit_error(
    billing_process_instance, caplog, existing_journal_file_response
):
    billing_process_instance.write_charges_file = AsyncMock(
        side_effect=JournalSubmitError("an error occurred.", journal_id="BJO-9000-4019")
    )
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements = AsyncMock(return_value=2)
    billing_process_instance.mpt_client = AsyncMock()
    billing_process_instance.mpt_client.count_active_agreements = AsyncMock(return_value=2)
    billing_process_instance.mpt_client.get_journal_by_authorization_external_id = AsyncMock(
        return_value=existing_journal_file_response["data"][0]
    )
    billing_process_instance.complete_journal_process = AsyncMock(return_value=None)
    response = await billing_process_instance.process()
    assert response.result is ProcessResult.ERROR
    assert response.journal_id == "BJO-9000-4019"
    assert response.message == "an error occurred."


# ------------------------------------------------------------------------------------
# - Test maybe_call()
@pytest.mark.asyncio()
async def test_maybe_call_dry_run_true(billing_process_instance):
    """if dry_run is True, the async function should NOT be executed."""
    mock_func = AsyncMock(return_value="should not be called")
    billing_process_instance.dry_run = True

    result = await billing_process_instance.maybe_call(mock_func, 1, key="value")

    mock_func.assert_not_awaited()
    assert result is None


@pytest.mark.asyncio()
async def test_maybe_call_dry_run_false(billing_process_instance):
    """if dry_run is False, the async function should be executed."""
    mock_func = AsyncMock(return_value="called")

    result = await billing_process_instance.maybe_call(mock_func, 1, key="value")

    mock_func.assert_awaited_once_with(1, key="value")
    assert result == "called"


# -----------------------------------------------------------------------------------
# - Test acquire_semaphore()


@pytest.mark.asyncio()
async def test_acquire_semaphore_acquires_and_releases(billing_process_instance):
    """the semaphore should be acquired and released once for each call"""
    semaphore = Mock()
    semaphore.acquire = AsyncMock()
    semaphore.release = Mock()
    billing_process_instance.semaphore = semaphore

    async with billing_process_instance.acquire_semaphore():
        semaphore.acquire.assert_awaited_once()
        semaphore.release.assert_not_called()

    semaphore.release.assert_called_once()


# -----------------------------------------------------------------------------------
# - Test build_filepath()
@pytest.mark.parametrize("dry_run", [True, False])
def test_build_filepath_formats_correctly(dry_run, billing_process_instance):
    """a file path should be generated differently based on the value of dry_run"""
    billing_process_instance.dry_run = dry_run

    result = billing_process_instance.build_filepath()
    expected_filename = "charges_AUT-5305-9928_2025_06.jsonl"

    if dry_run:
        assert result == expected_filename
    else:
        assert result.endswith(expected_filename)
        assert result.startswith(tempfile.gettempdir())


# -----------------------------------------------------------------------------------
# - Test process_billing()


@pytest.mark.asyncio()
@patch("app.billing.process_billing.MPTClient")
@patch("app.billing.process_billing.AuthorizationProcessor")
@patch("app.billing.process_billing.get_settings")
async def test_process_billing_with_single_authorization(
    mock_get_settings, mock_processor_cls, mock_client_cls
):
    """if the process_billing() is started with an authorization,
    it fetches the authorization's payload
    and process the related charges and the
    AuthorizationProcessor.process() will be called once"""
    mock_get_settings.return_value.mpt_product_id = "product_1"

    mock_authorization = {"id": "AUTH1"}
    mock_client = AsyncMock()
    mock_client.get_authorization = AsyncMock(return_value=mock_authorization)
    mock_client_cls.return_value = mock_client

    mock_processor = mock_processor_cls.return_value
    mock_processor.process = AsyncMock()

    from app.billing.process_billing import process_billing

    await process_billing(2025, 7, 5, "AUTH1", dry_run=True)

    mock_client.get_authorization.assert_awaited_once_with("AUTH1")
    mock_processor_cls.assert_called_once_with(2025, 7, mock_authorization, True)
    mock_processor.process.assert_awaited_once()


@pytest.mark.asyncio()
@patch("app.billing.process_billing.MPTClient")
@patch("app.billing.process_billing.AuthorizationProcessor")
@patch("app.billing.process_billing.get_settings")
@patch("app.billing.process_billing.send_notifications")
async def test_process_billing_with_multiple_authorizations(
    mock_notify, mock_get_settings, mock_processor_cls, mock_mpt_client_cls
):
    """if the process_billing() is started without a given authorization's ID,
    all the authorizations
    will be fetched and for each of them a task for calling the process()
    will be executed"""
    mock_get_settings.return_value.mpt_product_id = "product_1"
    mock_get_settings.return_value.ffc_billing_process_max_concurrency = 2

    async def async_gen():
        yield {"id": "AUTH1"}
        yield {"id": "AUTH2"}

    mock_mpt_client = AsyncMock()
    mock_mpt_client.get_authorizations_for_product = Mock(return_value=async_gen())
    mock_mpt_client.httpx_client = AsyncMock()
    mock_mpt_client.httpx_client.aclose = AsyncMock()
    mock_mpt_client_cls.return_value = mock_mpt_client

    mock_processor = mock_processor_cls.return_value
    mock_processor.process = AsyncMock()

    from app.billing.process_billing import process_billing

    await process_billing(2025, 7, cutoff_day=5)

    assert mock_processor_cls.call_count == 2
    assert mock_processor.process.await_count == 2
    mock_mpt_client.get_authorizations_for_product.assert_called_once()
    mock_mpt_client.httpx_client.aclose.assert_awaited_once()
    mock_notify.assert_awaited_once()
    _, kwargs = mock_notify.call_args
    assert kwargs["year"] == 2025
    assert kwargs["month"] == 7
    assert kwargs["cutoff_day"] == 5


# # -----------------------------------------------------------------------------------
# # - Test command
@pytest.mark.parametrize(
    ("opts", "not_allowed", "error_message"),
    [
        (
            {"year": 2025, "month": 8, "dry_run": True, "cutoff_day": 1},
            False,
            None,
        ),
        (
            {
                "year": 2025,
                "month": 12,
                "dry_run": False,
                "authorization": "AUTH123",
                "cutoff_day": 1,
            },
            False,
            None,
        ),
        (
            {
                "year": 2027,
                "month": 1,
                "dry_run": True,
                "cutoff_day": 5,
            },
            True,
            "The billing period cannot be in the future.",
        ),
        (
            {
                "year": 2026,
                "month": 4,
                "dry_run": True,
                "cutoff_day": 5,
            },
            True,
            "The billing period cannot be in the future.",
        ),
        (
            {
                "dry_run": True,
            },
            False,
            None,
        ),
        (
            {
                "year": 2026,
                "dry_run": True,
                "cutoff_day": 5,
            },
            False,
            None,
        ),
        (
            {
                "month": 2,
                "dry_run": True,
                "cutoff_day": 5,
            },
            False,
            None,
        ),
        (
            {
                "month": 20,
                "dry_run": True,
            },
            True,
            "The billing month must be between 1 and 12 (inclusive).",
        ),
        (
            {
                "cutoff_day": 100,
                "dry_run": True,
            },
            True,
            "The cutoff-day must be between 1 and 28 (inclusive).",
        ),
        (
            {
                "year": 2024,
                "month": 12,
                "dry_run": True,
                "cutoff_day": 5,
            },
            True,
            "The billing year must be",
        ),
    ],
)
@freeze_time("2026-03-16")
def test_process_billing_command(mocker, opts, not_allowed, error_message, capsys):
    import app.commands.process_billing as mod

    fake_coro = object()
    mock_process_billing = Mock(return_value=fake_coro)
    mock_asyncio_run = Mock()

    mocker.patch.object(mod, "process_billing", mock_process_billing)
    mocker.patch.object(mod.asyncio, "run", mock_asyncio_run)

    if not_allowed:
        with pytest.raises(typer.Exit) as excinfo:
            mod.command(**opts)

        assert excinfo.value.exit_code == 1

        captured = capsys.readouterr()
        assert error_message in captured.err

        mock_process_billing.assert_not_called()
        mock_asyncio_run.assert_not_called()
    else:
        mod.command(**opts)

        expected_year = opts.get("year", 2026)
        expected_month = opts.get("month", 2)

        mock_process_billing.assert_called_once_with(
            year=expected_year,
            month=expected_month,
            authorization_id=opts.get("authorization"),
            dry_run=opts.get("dry_run", False),
            cutoff_day=opts.get("cutoff_day", 5),
        )
        mock_asyncio_run.assert_called_once_with(fake_coro)


# # -----------------------------------------------------------------------------------


def test_count_process_result_no_errors(process_result_success_payload):
    success, fail = check_results(results=process_result_success_payload)
    assert success is True
    assert fail is False


def test_count_process_result_journal_skipped(process_result_with_warning):
    success, fail = check_results(results=process_result_with_warning)
    assert success is False
    assert fail is False


def test_count_process_result_error(process_result_with_error):
    success, fail = check_results(results=process_result_with_error)
    assert success is False
    assert fail is True


# # - Test Notifications


@pytest.mark.asyncio()
@patch("app.notifications.send_notification", new_callable=AsyncMock)
async def test_process_billing_results_success_notification(
    send_notification_mock, process_result_success_payload
):
    import app.billing.notification_helper as mod

    await mod.send_notifications(results=process_result_success_payload, year=2025, month=9)

    assert send_notification_mock.called


@freeze_time("2025-09-01")
@pytest.mark.asyncio()
@patch("app.notifications.send_notification", new_callable=AsyncMock)
async def test_process_billing_in_progress_notification(
    send_notification_mock, process_result_with_error, caplog
):
    import app.billing.notification_helper as mod

    with caplog.at_level("WARNING"):
        await mod.send_notifications(results=process_result_with_error, year=2025, month=9)
    assert send_notification_mock.called
    assert "Journals for the September-2025 billing cycle are in progress." in caplog.messages[0]


@freeze_time("2025-09-08")
@pytest.mark.asyncio()
@patch("app.notifications.send_notification", new_callable=AsyncMock)
async def test_process_billing_error_notification(
    send_notification_mock, process_result_with_error, caplog
):
    import app.billing.notification_helper as mod

    with caplog.at_level("ERROR"):
        await mod.send_notifications(results=process_result_with_error, year=2025, month=9)
    assert send_notification_mock.called
    assert "The billing process for September-2025 was completed with Errors." in caplog.messages[0]


# - test _safe_unlink()


@pytest.mark.asyncio()
async def test_safe_unlink_file_not_found(billing_process_instance, caplog):
    """Test _safe_unlink handles FileNotFoundError gracefully."""
    with patch("aiofiles.os.unlink", new_callable=AsyncMock) as mock_unlink:
        mock_unlink.side_effect = FileNotFoundError("File not found")
        with caplog.at_level(logging.DEBUG):
            await billing_process_instance._safe_unlink("/tmp/nonexistent_file.jsonl")

        assert mock_unlink.called
        # Should log at DEBUG level for FileNotFoundError
        assert "File /tmp/nonexistent_file.jsonl not found during cleanup, ignoring" in caplog.text


@pytest.mark.asyncio()
async def test_safe_unlink_generic_exception(billing_process_instance, caplog):
    """Test _safe_unlink handles generic exceptions with warning log."""
    error = PermissionError("Permission denied")
    with patch("aiofiles.os.unlink", new_callable=AsyncMock) as mock_unlink:
        mock_unlink.side_effect = error
        with caplog.at_level(logging.WARNING):
            await billing_process_instance._safe_unlink("/tmp/protected_file.jsonl")

        assert mock_unlink.called
        # Should log at WARNING level for generic exceptions
        assert "Failed to cleanup file /tmp/protected_file.jsonl: Permission denied" in caplog.text


@pytest.mark.asyncio()
async def test_safe_unlink_generic_exception_with_custom_error_message(
    billing_process_instance, caplog
):
    """Test _safe_unlink handles generic exceptions with various error types."""
    error = OSError("I/O error occurred")
    with patch("aiofiles.os.unlink", new_callable=AsyncMock) as mock_unlink:
        mock_unlink.side_effect = error
        with caplog.at_level(logging.WARNING):
            await billing_process_instance._safe_unlink("/tmp/io_error_file.jsonl")

        assert mock_unlink.called
        assert "Failed to cleanup file /tmp/io_error_file.jsonl: I/O error occurred" in caplog.text


@pytest.mark.asyncio()
async def test_safe_unlink_success(billing_process_instance):
    """Test _safe_unlink successfully removes a file."""
    with patch("aiofiles.os.unlink", new_callable=AsyncMock) as mock_unlink:
        await billing_process_instance._safe_unlink("/tmp/valid_file.jsonl")

        assert mock_unlink.called
        mock_unlink.assert_called_once_with("/tmp/valid_file.jsonl")

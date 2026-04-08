from _decimal import Decimal
from dataclasses import dataclass
from datetime import date
from typing import Any, TypedDict

from app.billing.enum import ProcessResult


class AuthBillingProcess:
    pass


@dataclass
class Datasource:
    linked_datasource_id: str
    linked_datasource_type: str
    datasource_id: str
    datasource_name: str


@dataclass
class Refund:
    amount: Decimal
    start_date: date
    end_date: date
    description: str


@dataclass
class TrialInfo:
    trial_days: set[int]
    refund_from: date
    refund_to: date


@dataclass
class CurrencyConversionInfo:
    base_currency: str
    billing_currency: str
    exchange_rate: Decimal
    exchange_rates: dict[str, Any] | None = None


@dataclass
class ProcessResultInfo:
    authorization_id: str
    result: ProcessResult
    journal_id: str | None = None
    message: str | None = None


@dataclass
class ProcessResultSummary(TypedDict):
    successful_counter: int
    error_counter: int
    details: list

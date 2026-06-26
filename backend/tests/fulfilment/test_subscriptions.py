from unittest.mock import AsyncMock, Mock

import pytest

from app.fulfilment.subscriptions import (
    create_order_subscription,
    get_subscription_by_line_and_item_id,
)


def _subscription(sub_id: str, lines: list[dict]) -> dict:
    return {"id": sub_id, "lines": lines}


def _line(line_id: str, item_id: str) -> dict:
    return {"id": line_id, "item": {"id": item_id}}


def test_returns_subscription_when_line_and_item_match():
    sub = _subscription("SUB-1", [_line("ALI-0001", "ITM-0001")])

    result = get_subscription_by_line_and_item_id([sub], item_id="ITM-0001", line_id="ALI-0001")

    assert result is sub


def test_returns_correct_subscription_among_many():
    sub1 = _subscription("SUB-1", [_line("ALI-0001", "ITM-0001")])
    sub2 = _subscription("SUB-2", [_line("ALI-0002", "ITM-0002")])

    result = get_subscription_by_line_and_item_id(
        [sub1, sub2], item_id="ITM-0002", line_id="ALI-0002"
    )

    assert result is sub2


def test_matches_within_subscription_with_multiple_lines():
    sub = _subscription(
        "SUB-1",
        [_line("ALI-0001", "ITM-0001"), _line("ALI-0002", "ITM-0002")],
    )

    result = get_subscription_by_line_and_item_id([sub], item_id="ITM-0002", line_id="ALI-0002")

    assert result is sub


def test_returns_none_when_line_id_matches_but_item_id_does_not():
    sub = _subscription("SUB-1", [_line("ALI-0001", "ITM-0001")])

    result = get_subscription_by_line_and_item_id([sub], item_id="ITM-9999", line_id="ALI-0001")

    assert result is None


def test_returns_none_when_item_id_matches_but_line_id_does_not():
    sub = _subscription("SUB-1", [_line("ALI-0001", "ITM-0001")])

    result = get_subscription_by_line_and_item_id([sub], item_id="ITM-0001", line_id="ALI-9999")

    assert result is None


def test_returns_none_for_empty_subscriptions():
    result = get_subscription_by_line_and_item_id([], item_id="ITM-0001", line_id="ALI-0001")

    assert result is None


def test_returns_none_when_subscription_has_no_lines():
    sub = _subscription("SUB-1", [])

    result = get_subscription_by_line_and_item_id([sub], item_id="ITM-0001", line_id="ALI-0001")

    assert result is None


@pytest.mark.parametrize(
    ("item_id", "line_id", "expected_id"),
    [
        ("ITM-0001", "ALI-0001", "SUB-1"),
        ("ITM-0002", "ALI-0002", "SUB-2"),
        ("ITM-0001", "ALI-0002", None),  # line/item belong to different subscriptions
    ],
)
def test_line_and_item_must_belong_to_same_subscription(item_id, line_id, expected_id):
    subscriptions = [
        _subscription("SUB-1", [_line("ALI-0001", "ITM-0001")]),
        _subscription("SUB-2", [_line("ALI-0002", "ITM-0002")]),
    ]

    result = get_subscription_by_line_and_item_id(subscriptions, item_id=item_id, line_id=line_id)

    assert (result["id"] if result else None) == expected_id


async def test_create_order_subscription_skips_when_subscription_already_exists():
    order = {
        "id": "ORD-1111-2222-3333",
        "lines": [
            {"id": "ALI-0001", "item": {"id": "ITM-0001", "name": "FinOps for Cloud"}},
        ],
        "subscriptions": [
            _subscription("SUB-1", [_line("ALI-0001", "ITM-0001")]),
        ],
    }
    ext_client = AsyncMock()
    organization = Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")

    await create_order_subscription(ext_client, order, organization)

    ext_client.create_subscription.assert_not_awaited()

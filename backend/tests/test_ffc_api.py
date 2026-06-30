from app.api_clients.ffc_api import resolve_params


def test_resolve_params_empty_when_no_arguments() -> None:
    """`resolve_params` returns an empty list when no limit, offset, or rql is given."""
    assert resolve_params() == []


def test_resolve_params_includes_limit_and_offset() -> None:
    """`resolve_params` emits stringified limit and offset tuples when provided."""
    assert resolve_params(limit=10, offset=5) == [("limit", "10"), ("offset", "5")]


def test_resolve_params_keeps_zero_limit_and_offset() -> None:
    """`resolve_params` includes limit/offset of 0 since only `None` is skipped."""
    assert resolve_params(limit=0, offset=0) == [("limit", "0"), ("offset", "0")]


def test_resolve_params_splits_rql_clauses() -> None:
    """`resolve_params` splits an `&`-joined rql string into individual empty-valued clauses."""
    assert resolve_params(rql="eq(a,1)&eq(b,2)") == [("eq(a,1)", ""), ("eq(b,2)", "")]


def test_resolve_params_combines_pagination_and_rql() -> None:
    """`resolve_params` combines pagination params and rql clauses in order."""
    assert resolve_params(limit=1, offset=2, rql="eq(a,1)") == [
        ("limit", "1"),
        ("offset", "2"),
        ("eq(a,1)", ""),
    ]

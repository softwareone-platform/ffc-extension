from decimal import Decimal


def find_first(func, iterable, default=None):
    return next(filter(func, iterable), default)


def compute_daily_expenses(
    cumulative_expenses: dict[int, Decimal], last_day_of_month: int
) -> dict[int, Decimal]:
    """
    This function computes the daily expenses based on the given cumulative expenses.
    It also fills in any missing days using the previous days' cumulative value.
    Args:
        cumulative_expenses: dict[int,Decimal]: the original cumulative expenses dictionary
        last_day_of_month: the last day of the month
    Returns:
        daily_expenses: dict[int,Decimal]: the daily expenses dictionary
    """
    daily_expenses = {}
    previous_amount = Decimal(0)
    for day in range(1, last_day_of_month + 1):
        current = Decimal(cumulative_expenses.get(day, previous_amount))
        daily_expenses[day] = Decimal(current - previous_amount)
        previous_amount = current
    return daily_expenses


async def async_groupby(
    iterable,
    key,
):
    current_group = []
    current_key = None
    first_item = True

    async for item in iterable:
        k = key(item)
        if first_item:
            current_key = k
            current_group.append(item)
            first_item = False
        elif k == current_key:
            current_group.append(item)
        else:
            yield current_key, current_group
            current_key = k
            current_group = [item]

    if current_group:
        yield current_key, current_group

from app.db import models


def render_budget_item(budget: models.Budget) -> str:
    return f"{budget.currency}, {len(budget.entries)} операций"


def render_category_item(category: models.EntryCategory) -> str:
    category_type = (
        lambda category: "расходы"
        if category.type.value == "expenses"
        else "доходы"
    )

    rendered = (
        f"{category.name} ({category_type(category)}), "
        f"{len(category.entries)} операций"
    )

    return rendered


def render_entry_item(entry: models.Entry) -> str:
    sign = "+" if entry.sum > 0 else "-"
    pretty_sum = f"{sign}{entry.sum_ / 100:.2f}"
    pretty_date = f"{entry.transaction_date:%Y-%m-%d %H:%M:%S}"
    rendered = (
        "Новая транзакция успешно создана.\n"
        f"{pretty_sum} {entry.budget.currency.value}, "
        f"{entry.category.name}, {pretty_date}"
    )
    if entry.description:
        rendered += f", {entry.description}"

    return rendered

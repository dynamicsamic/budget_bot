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
    pretty_sum = f"{entry.sum / 100:.2f}"
    if entry.sum > 0:
        pretty_sum = "+" + pretty_sum
    pretty_date = f"{entry.transaction_date:%Y-%m-%d %H:%M:%S}"
    rendered = (
        f"{pretty_sum} {entry.budget.currency.value}, "
        f"{entry.category.name}, {pretty_date}"
    )
    if entry.description:
        rendered += f", {entry.description}"

    return rendered

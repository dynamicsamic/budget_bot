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

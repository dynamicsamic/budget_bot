from aiogram.filters.callback_data import CallbackData


class ReportTypeCallback(CallbackData, prefix="report"):
    type: str
    period: str


class BudgetItemActionData(CallbackData, prefix="action_budget_item"):
    budget_id: str
    action: str

from aiogram.filters.callback_data import CallbackData

from app.bot import shared


class SignupUserCallbackData(CallbackData, prefix=shared.signup_user):
    action: str


class UpdateBudgetCurrencyCallbackData(
    CallbackData, prefix=shared.update_budget_currency
):
    action: str


class ReportTypeCallback(CallbackData, prefix="report"):
    type: str
    period: str


class CategoryItemActionData(CallbackData, prefix="category_action"):
    action: str
    category_id: int


class UpdateCategoryChooseAttribute(CallbackData, prefix="update_category"):
    attribute: str


class EntryItemActionData(CallbackData, prefix="action_entry_item"):
    entry_id: str
    action: str

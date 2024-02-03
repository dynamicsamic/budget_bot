from aiogram.filters.callback_data import CallbackData


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

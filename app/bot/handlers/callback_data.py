from aiogram.filters.callback_data import CallbackData


class ReportTypeCallback(CallbackData, prefix="report"):
    type: str
    period: str

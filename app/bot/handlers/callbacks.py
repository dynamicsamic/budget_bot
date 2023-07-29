from aiogram import Router, types
from aiogram.filters.text import Text

from app.bot.keyboards import choose_period_kb
from app.bot.middlewares import DateInfoMiddleware
from app.utils import DateGen

from .callback_data import ReportTypeCallback

router = Router()
router.callback_query.middleware(DateInfoMiddleware())


@router.callback_query(Text("check_income"))
async def cb_check_income(callback: types.CallbackQuery):
    await callback.message.answer(
        "Выберите период", reply_markup=choose_period_kb("income").as_markup()
    )
    await callback.answer()


@router.callback_query(ReportTypeCallback.filter())
async def cb_build_report(
    callback: types.CallbackQuery,
    callback_data: ReportTypeCallback,
    date_info: DateGen,
):
    p = callback_data.period
    t = callback_data.type

    await callback.message.answer(str(date_info))
    print(callback_data.period, callback_data.type)
    await callback.answer()


def foo(type: str, period: str):
    manager = []
    cb = []
    if hasattr(manager, period):
        getattr(manager, period)(cb.date_info)

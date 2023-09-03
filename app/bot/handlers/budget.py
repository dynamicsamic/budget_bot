from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext

from app.bot import keyboards
from app.bot.middlewares import DataBaseSessionMiddleWare
from app.db.managers import ModelManager
from app.db.models import User

from .states import BudgetState

router = Router()
router.message.middleware(DataBaseSessionMiddleWare())
router.callback_query.middleware(DataBaseSessionMiddleWare())


@router.message(Command("budget_create"))
async def cmd_create_budget(message: types.Message, state: FSMContext):
    await message.answer(
        """Для того, чтобы создать бюджет, введите наименование валюты. 
            Наименование должно содержать только буквы (в любом регистре) 
            и быть короче 10 символов. Отдавайте предпочтение общепринятым сокращениям, 
            например RUB или USD"""
    )

    await state.set_state(BudgetState.currency)


@router.message(BudgetState.currency)
async def create_budget_finish(
    message: types.Message,
    state: FSMContext,
    model_managers: dict[str, Type[ModelManager]],
    user: User,
):
    currency = message.text
    if not currency.isalpha() or len(currency) > 10:
        await message.answer(
            """
            Неверный формат обозначения валюты.
            Наименование должно содержать только буквы (в любом регистре) 
            и быть короче 10 символов. Отдавайте предпочтение общепринятым сокращениям, 
            например RUB или USD
            """
        )
        return
    await state.clear()

    budgets = model_managers["budget"]
    created = budgets.create(
        currency=currency, user_id=user.id, name=f"user{user.tg_id}_{currency}"
    )
    if created:
        await message.answer(
            "Вы успешно создали новый личный бюджет. Можете добавить новые транзакции или категории."
        )
    else:
        await message.answer(
            "Что-то пошло не так при создании нового бюджета. Обратитесь в поддержку"
        )


@router.callback_query(Text("budget_menu"))
async def budget_menu(callback: types.CallbackQuery):
    await callback.message.answer(
        "Управление бюджетами", reply_markup=keyboards.budget_menu.as_markup()
    )
    await callback.answer()


@router.callback_query(Text("budget_list"))
async def budget_list(
    callback: types.CallbackQuery,
    user: User,
):
    await callback.message.answer(f"Ваши бюджеты: {user.budgets}")
    await callback.answer()


@router.callback_query(Text("budget_create"))
async def budget_create(
    callback: types.CallbackQuery,
    user: User,
):
    pass


@router.callback_query(Text("budget_delete"))
async def budget_delete(
    callback: types.CallbackQuery,
    user: User,
):
    pass

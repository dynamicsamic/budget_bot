from typing import Type

from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from app.bot.keyboards import signup_to_proceed
from app.bot.middlewares import DataBaseSessionMiddleWare
from app.db.managers import ModelManager
from app.db.models import User

from .states import BudgetState

router = Router()
router.message.middleware(DataBaseSessionMiddleWare())


@router.message(Command("budget_create"))
async def cmd_create_budget(
    message: types.Message, state: FSMContext, user: User
):
    if user is None:
        await message.answer(
            "Для продолжения необходимо зарегистрироваться. "
            "От Вас не потребуется вводить никакие данные.",
            reply_markup=signup_to_proceed,
        )
        return

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

    mgr = model_managers["budget"]
    created = mgr.create(
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

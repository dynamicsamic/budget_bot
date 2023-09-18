from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext

from app.bot import keyboards
from app.bot.middlewares import DataBaseSessionMiddleWare
from app.db.managers import ModelManager
from app.db.models import User

from .callback_data import BudgetItemActionData
from .states import BudgetCreatetState, BudgetUpdateState

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

    await state.set_state(BudgetCreatetState.currency)


@router.message(BudgetCreatetState.currency)
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


@router.callback_query(Text("budget_create"))
async def budget_create(callback: types.CallbackQuery, state: FSMContext):
    await cmd_create_budget(callback.message, state)
    await callback.answer()


@router.message(Command("show_budgets"))
async def cmd_show_budgets(
    message: types.Message, user: User, state: FSMContext
):
    budgets = user.budgets
    if not budgets:
        await cmd_create_budget(message, state)
    else:
        await message.answer(
            "Кликните на нужный бюджет, чтобы выбрать действие",
            reply_markup=keyboards.budget_item_list_interactive(budgets),
        )


@router.callback_query(Text("budget_menu"))
async def show_budgets(
    callback: types.CallbackQuery, user: User, state: FSMContext
):
    await cmd_show_budgets(callback.message, user, state)
    await callback.answer()


@router.callback_query(F.data.startswith("budget_item"))
async def budget_item_show_options(callback: types.CallbackQuery):
    budget_id = callback.data.rsplit("_", maxsplit=1)[-1]
    await callback.message.answer(
        "Выберите действие",
        reply_markup=keyboards.budget_item_choose_action(budget_id),
    )
    await callback.answer()


@router.callback_query(BudgetItemActionData.filter(F.action == "delete"))
async def budget_item_delete(
    callback: types.CallbackQuery,
    callback_data: BudgetItemActionData,
    model_managers: dict[str, Type[ModelManager]],
):
    deleted = model_managers["budget"].delete(id=callback_data.budget_id)
    if deleted:
        await callback.message.answer("Бюджет был успешно удален")
    else:
        await callback.message.answer(
            "Ошибка удаления бюджета. Бюджет отсутствует или был удален ранее."
        )
    await callback.answer()


@router.callback_query(BudgetItemActionData.filter(F.action == "update"))
async def budget_item_update_recieve_currency(
    callback: types.CallbackQuery,
    callback_data: BudgetItemActionData,
    state: FSMContext,
):
    await state.set_state(BudgetUpdateState.currency)
    await state.set_data({"budget_id": callback_data.budget_id})
    await callback.message.answer(
        "Введите новую валюту бюджета.Наименование должно содержать только буквы (в любом регистре) "
        "и быть короче 10 символов. Отдавайте предпочтение общепринятым сокращениям, "
        "например RUB или USD"
    )
    await callback.answer()


@router.message(BudgetUpdateState.currency)
async def budget_item_update_finish(
    message: types.Message,
    state: FSMContext,
    model_managers: dict[str, Type[ModelManager]],
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

    data = await state.get_data()
    budget_id = data["budget_id"]
    updated = model_managers["budget"].update(id_=budget_id, currency=currency)
    if updated:
        await message.answer("Бюджет был успешно обновлен")
    else:
        await message.answer(
            "Ошибка обновления бюджета. Бюджет отсутствует или был удален ранее."
        )
    await state.clear()

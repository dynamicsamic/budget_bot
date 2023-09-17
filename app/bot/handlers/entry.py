from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext

from app.bot import keyboards
from app.bot.middlewares import DataBaseSessionMiddleWare
from app.db.managers import ModelManager
from app.db.models import EntryType, User

from .callback_data import CategoryItemActionData
from .states import EntryCreateState

router = Router()
router.message.middleware(DataBaseSessionMiddleWare())
router.callback_query.middleware(DataBaseSessionMiddleWare())


@router.message(Command("entry_create"))
async def cmd_create_entry(
    message: types.Message, state: FSMContext, user: User
):
    await message.answer(
        "Создаем новую транзакцию.\nВыберите бюджет",
        reply_markup=keyboards.create_entry_show_budgets(user.budgets),
    )
    await state.set_state(EntryCreateState.budget_id)


@router.callback_query(
    EntryCreateState.budget_id, F.data.startswith("entry_budget_item")
)
async def create_entry_recieve_category(
    callback: types.CallbackQuery,
    state: FSMContext,
    model_managers: dict[str, Type[ModelManager]],
    user: User,
):
    *_, budget_id = callback.data.rsplit("_", maxsplit=1)
    if not model_managers["budget"].exists(budget_id):
        await callback.message.answer(
            "Указан неверный бюджет.\n" "Выберите бюджет из списка ниже.",
            reply_markup=keyboards.create_entry_show_budgets(user.budgets),
        )
        return

    await state.update_data(budget_id=budget_id)
    await callback.message.answer(
        "Выберите категорию",
        reply_markup=keyboards.create_entry_show_categories(user.categories),
    )
    await state.set_state(EntryCreateState.category_id)
    await callback.answer()


@router.callback_query(
    EntryCreateState.category_id, F.data.startswith("entry_category_item")
)
async def create_entry_recieve_category(
    callback: types.CallbackQuery,
    state: FSMContext,
    model_managers: dict[str, Type[ModelManager]],
    user: User,
):
    *_, category_id = callback.data.rsplit("_", maxsplit=1)
    if not model_managers["category"].exists(category_id):
        await callback.message.answer(
            "Выбрана несуществуюшая.\n" "Выберите категорию из списка ниже.",
            reply_markup=keyboards.create_entry_show_categories(
                user.categories
            ),
        )
        return

    await state.update_data(category_id=category_id)


"""
enter_sum
enter_transaction_date
enter_description
"""

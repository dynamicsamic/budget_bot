import re
from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext

from app.bot import keyboards
from app.bot.middlewares import DataBaseSessionMiddleWare
from app.db.managers import ModelManager
from app.db.models import EntryType, User

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
    await callback.message.answer(
        "Введите сумму транзакции.\n"
        "Допустимые виды записи: 1521; 100,91; 934.2; 1 445.67"
    )
    await state.set_state(EntryCreateState.sum)
    await callback.answer()


def validate_sum(raw_sum: str) -> tuple[int, str]:
    invalid = 0
    if len(raw_sum) >= 20:
        return invalid, "Задано слишком длинное число."
    cleaned_sum = re.sub(",", ".", re.sub("\s", "", raw_sum))
    try:
        valid_float = round(float(cleaned_sum), 2)
    except ValueError:
        error_message = (
            "Неверный формат суммы.\n"
            "Допустимые форматы: 1521; 100,91; 934.2; 1 445.67"
        )
        return invalid, error_message
    validated = int(valid_float * 100)
    if validated == invalid:
        return invalid, "Сумма не может быть равна 0."
    return validated, ""


@router.message(EntryCreateState.sum)
async def create_entry_recieve_sum(message: types.Message, state: FSMContext):
    validated_sum, error_message = validate_sum(message.text)
    if not validated_sum:
        await message.answer(error_message)
        return
    await state.update_data(sum=validated_sum)
    await message.answer(
        "Введите дату транзакции.\n"
        "Отправьте пустое сообщение, если транзакция выполнена сегодня."
    )
    await state.set_state(EntryCreateState.transcation_date)


"""
enter_transaction_date
enter_description
"""

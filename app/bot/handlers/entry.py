import datetime as dt
from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext

from app import settings
from app.bot import keyboards
from app.bot.filters import (
    EntryBudgetIdFilter,
    EntryCategoryIdFilter,
    EntryDateFilter,
    EntrySumFilter,
)
from app.bot.middlewares import ModelManagerMiddleware
from app.bot.states import EntryCreateState, EntryList
from app.db.managers import (
    DateQueryManager,
    EntryManager,
    ModelManager,
    ModelManagerStore,
)
from app.db.models import User

router = Router()
router.message.middleware(ModelManagerMiddleware())
router.callback_query.middleware(ModelManagerMiddleware())


@router.message(Command("entry_create"))
async def cmd_create_entry(
    message: types.Message, state: FSMContext, user: User
):
    await message.answer(
        "Создаем новую транзакцию.\nВыберите бюджет",
        reply_markup=keyboards.create_entry_show_budgets(user.budgets),
    )
    await state.set_state(EntryCreateState.budget)


@router.callback_query(
    EntryCreateState.budget,
    EntryBudgetIdFilter(),
    flags=ModelManagerStore.as_flags("budget"),
)
async def create_entry_receive_category(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    budget_id: int,
    budget_manager: DateQueryManager,
):
    budget = budget_manager.get(budget_id)
    if not budget:
        await callback.message.answer(
            "Указан неверный бюджет.\n" "Выберите бюджет из списка ниже.",
            reply_markup=keyboards.create_entry_show_budgets(user.budgets),
        )
        return

    await state.update_data(budget=budget)
    await callback.message.answer(
        "Выберите категорию",
        reply_markup=keyboards.create_entry_show_categories(user.categories),
    )
    await state.set_state(EntryCreateState.category)
    await callback.answer()


@router.callback_query(
    EntryCreateState.category,
    EntryCategoryIdFilter(),
    flags=ModelManagerStore.as_flags("category"),
)
async def create_entry_receive_category(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    category_id: int,
    category_manager: DateQueryManager,
):
    category = category_manager.get(category_id)
    if not category:
        await callback.message.answer(
            "Выбрана несуществуюшая.\n" "Выберите категорию из списка ниже.",
            reply_markup=keyboards.create_entry_show_categories(
                user.categories
            ),
        )
        return

    await state.update_data(category=category)
    await callback.message.answer(
        "Введите сумму транзакции.\n"
        "Допустимые виды записи: 1521; 100,91; 934.2; 1 445.67"
    )
    await state.set_state(EntryCreateState.sum)
    await callback.answer()


@router.message(EntryCreateState.sum, EntrySumFilter())
async def create_entry_receive_sum(
    message: types.Message,
    state: FSMContext,
    transaction_sum: int,
    error_message: str,
):
    if not transaction_sum:
        await message.answer(error_message)
        return

    data = await state.get_data()

    entry_type = data["category"].type
    if entry_type.value == "expenses":
        transaction_sum = -transaction_sum

    await state.update_data(sum=transaction_sum)
    await message.answer(
        "Введите дату транзакции.\n"
        "Отправьте точку `.`, если транзакция выполнена сегодня.\n"
        "Допустимые форматы: дд мм гггг, дд-мм-гггг, ддммгггг."
    )
    await state.set_state(EntryCreateState.transcation_date)


@router.message(EntryCreateState.transcation_date, EntryDateFilter())
async def create_entry_receive_transaction_date(
    message: types.Message,
    state: FSMContext,
    transaction_date: dt.datetime,
    error_message: str,
):
    if not transaction_date:
        await message.answer(error_message)
        return
    await state.update_data(transaction_date=transaction_date)
    await message.answer(
        "При необходимости добавьте комментарий к транзакции\n"
        "Отправьте точку `.`, если комментарий не требуется"
    )
    await state.set_state(EntryCreateState.description)


@router.message(
    EntryCreateState.description,
    flags=ModelManagerStore.as_flags("entry", "category"),
)
async def create_entry_receive_description(
    message: types.Message,
    state: FSMContext,
    entry_manager: EntryManager,
    category_manager: DateQueryManager,
):
    description = message.text
    if description == ".":
        description = None

    data = await state.get_data()
    budget = data["budget"]
    category = data["category"]
    sum_ = data["sum"]
    date = data["transaction_date"]
    created = entry_manager.create(
        budget_id=budget.id,
        category_id=category.id,
        sum=sum_,
        transaction_date=date,
        description=description,
    )
    if created:
        pretty_sum = f"{sum_ / 100:.2f}"
        pretty_date = f"{date:%Y-%m-%d %H:%M:%S}"
        success_msg = (
            "Новая транзакция успешно создана.\n"
            f"{pretty_sum} {budget.currency.value}, "
            f"{category.name}, {pretty_date}"
        )
        if description:
            success_msg += f", {description}"

        await message.answer(success_msg)

        category_manager.update(
            category.id, last_used=message.date.astimezone(settings.TIME_ZONE)
        )
    else:
        await message.answer(
            "Что-то пошло не так при создании транзакции."
            "Обратитесь в поддержку"
        )
    await state.clear()


@router.callback_query(F.data == "entry_create")
async def entry_create(callback: types.CallbackQuery, state: FSMContext):
    await cmd_create_entry(callback.message, state)
    await callback.answer()


@router.message(
    Command("show_entries"), flags=ModelManagerStore.as_flags("budget")
)
async def cmd_show_entries(
    message: types.Message,
    state: FSMContext,
    user: User,
    budget_manager: DateQueryManager,
):
    budgets = budget_manager.select(filters=[f"user_id=={user.id}"])
    await message.answer(
        "Выберите бюджет для просмотра транзакций",
        reply_markup=keyboards.create_entry_show_budgets(budgets),
    )
    await state.set_state(EntryList.budgets)


@router.callback_query(
    EntryList.budgets,
    EntryBudgetIdFilter(),
    flags=ModelManagerStore.as_flags("entry"),
)
async def entry_list(
    callback: types.CallbackQuery, budget_id: int, entry_manager: EntryManager
):
    entries = entry_manager.select(filters=[f"budget_id==1"])
    await callback.message.answer("hello")
    await callback.message.answer(
        "Нажмите на транзакцию, чтобы выбрать действие",
        reply_markup=keyboards.entry_item_list_interactive(entries),
    )
    await callback.answer()

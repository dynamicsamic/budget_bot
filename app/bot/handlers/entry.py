import datetime as dt

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session, scoped_session

from app import settings
from app.bot import filters, states
from app.bot.replies import keyboards
from app.bot.middlewares import EntryRepositoryMiddleWare
from app.db.models import User
from app.db.repository import CategoryRepository, EntryRepository

router = Router()

router.message.middleware(EntryRepositoryMiddleWare())
router.callback_query.middleware(EntryRepositoryMiddleWare())


@router.message(Command("entry_create"))
async def cmd_create_entry(
    message: types.Message,
    state: FSMContext,
    user: User,
    db_session: Session | scoped_session,
):
    await message.answer(
        "Создаем новую транзакцию.\nВыберите бюджет",
        reply_markup=keyboards.create_entry_show_budgets(
            # get_user_budgets(db_session, user.id)
        ),
    )
    await state.set_state(states.CreateEntry.budget)


@router.callback_query(
    states.CreateEntry.budget,
    filters.EntryBudgetIdFilter(),
)
async def create_entry_receive_category(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    ca_repository: CategoryRepository,
):
    await callback.message.answer(
        "Выберите категорию",
        reply_markup=keyboards.create_entry_show_categories(
            ca_repository.get_user_categories(user.id)
        ),
    )
    await state.set_state(states.CreateEntry.category)
    await callback.answer()


@router.callback_query(
    states.CreateEntry.category,
    filters.EntryCategoryIdFilter(),
)
async def create_entry_receive_category2(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    category_id: int,
    ca_repository: CategoryRepository,
):
    category = ca_repository.get_category(category_id)
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
    await state.set_state(states.CreateEntry.sum)
    await callback.answer()


@router.message(states.CreateEntry.sum, filters.EntrySumFilter())
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
    await state.set_state(states.CreateEntry.transcation_date)


@router.message(states.CreateEntry.transcation_date, filters.EntryDateFilter())
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
    await state.set_state(states.CreateEntry.description)


@router.message(
    states.CreateEntry.description,
)
async def create_entry_receive_description(
    message: types.Message,
    state: FSMContext,
    user: User,
    ca_repository: CategoryRepository,
    en_repository: EntryRepository,
):
    description = message.text
    if description == ".":
        description = None

    data = await state.get_data()
    category = data["category"]
    sum_ = data["sum"]
    date = data["transaction_date"]
    created = en_repository.create_entry(
        user.id,
        category_id=category.id,
        sum=sum_,
        transaction_date=date,
        description=description,
    )
    if created:
        await message.answer(
            f"Новая транзакция успешно создана: {created.render()}"
        )

        ca_repository.update_category(
            category.id,
            {
                "last_used": message.date.astimezone(settings.TIME_ZONE),
                "num_entries": category.num_entries + 1,
            },
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
    Command("manage_entries"),
)
async def cmd_manage_entries(
    message: types.Message,
    state: FSMContext,
    user: User,
    db_session: Session | scoped_session,
):
    # budgets = get_user_budgets(db_session, user.id)
    budgets = True
    await message.answer(
        "Для просмотра транзакций выберите бюджет",
        reply_markup=keyboards.create_entry_show_budgets(budgets),
    )
    await state.set_state(states.PreProcessEntry.choose_budget)


@router.callback_query(
    states.PreProcessEntry.choose_budget,
    filters.EntryBudgetIdFilter(),
)
async def manage_entry_choose_category(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    budget_id: str,
    ca_repository: CategoryRepository,
):
    await state.update_data(budget_id=budget_id)
    categories = ca_repository.get_user_categories(user.id)
    await callback.message.answer(
        "Выберите категорию",
        reply_markup=keyboards.create_entry_show_categories(categories),
    )
    await state.set_state(states.PreProcessEntry.choose_category)


@router.callback_query(
    states.PreProcessEntry.choose_category, filters.EntryCategoryIdFilter()
)
async def manage_entry_choose_entry(
    callback: types.CallbackQuery,
    state: FSMContext,
    category_id: int,
    en_repository: EntryRepository,
):
    entries = en_repository.get_category_entries(category_id)
    await callback.message.answer(
        "Нажмите на транзакцию, чтобы выбрать действие",
        reply_markup=keyboards.entry_item_list_interactive(entries),
    )
    await callback.answer()
    await state.set_state(states.PreProcessEntry.choose_entry)


@router.callback_query(
    states.PreProcessEntry.choose_entry, filters.GetEntryId()
)
async def entry_show_options(
    callback: types.CallbackQuery, state: FSMContext, entry_id: str
):
    await state.update_data(entry_id=entry_id)
    await callback.message.answer(
        "Выберите действие",
        reply_markup=keyboards.entry_item_choose_action2(),
    )
    await state.set_state(states.PreProcessEntry.choose_action)


@router.callback_query(
    states.PreProcessEntry.choose_action,
    F.data.startswith("entry_item_action"),
)
async def entry_delete_or_update(
    callback: types.CallbackQuery, state: FSMContext
):
    *_, action = callback.data.rsplit("_", maxsplit=1)
    if action == "delete":
        data = await state.get_data()
        entry_id = data["entry_id"]
        await callback.message.answer(
            "Вы уверены, что хотите удалить запись",
            reply_markup=keyboards.entry_confirm_delete(entry_id),
        )
        await state.clear()
        await state.set_state(states.DeleteEntry.confirm)
    elif action == "update":
        pass


@router.callback_query(
    states.DeleteEntry.confirm,
    filters.GetEntryId(),
)
async def entry_delete_confirm(
    callback: types.CallbackQuery,
    state: FSMContext,
    entry_id: int,
    en_repository: EntryRepositoryMiddleWare,
):
    deleted = en_repository.delete_entry(entry_id)
    msg = (
        "Транзакция успешно удалена"
        if deleted
        else "Ошибка удаления транзакции"
    )
    await callback.message.answer(msg)
    await callback.answer()
    await state.clear()


@router.callback_query(states.DeleteEntry.confirm)
async def entry_delete_cancel(
    callback: types.CallbackQuery, state: FSMContext
):
    await callback.message.answer("Удаление транзакции отменено")
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == "entry_menu")
async def show_entries(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    db_session: Session | scoped_session,
):
    await cmd_manage_entries(callback.message, state, user, db_session)
    await callback.answer()

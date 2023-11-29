from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session, scoped_session

from app.bot import keyboards
from app.bot.callback_data import BudgetItemActionData
from app.bot.filters import BudgetCurrencyFilter, BudgetNameFilter
from app.bot.states import BudgetCreatetState, BudgetUpdateState
from app.db.models import User
from app.services.budget import (
    count_user_budgets,
    create_budget,
    delete_budget,
    get_user_budgets,
    update_budget,
)

router = Router()


@router.message(Command("create_budget"))
async def cmd_create_budget(message: types.Message, state: FSMContext):
    await message.answer(
        "Добро пожаловать в меню создания бюджета.\n"
        "Начните создание нового бюджета с выбора подходящего названия.\n"
        "Функциональное имя сделает процесс работы с бюджетами более удобным.\n"
        "Хорошими вариантами будут: `Общий`, `Семейный`, `Инвестиционный` "
        "и так далее.\n"
        "В названии бюджета можно использовать только буквы и цифры."
        "Пробел и иные дополнительные символы недопустимы.\n"
        "Для разделения слов используйте тире и нижнее подчеркивание.\n"
        "Вам необходимо уложиться в 25 символов.\n"
        "Имена Ваших бюджетов не должны повторяться.",
        reply_markup=keyboards.button_menu(keyboards.buttons.main_menu),
    )

    await state.set_state(BudgetCreatetState.name)


@router.message(BudgetCreatetState.name, BudgetNameFilter())
async def create_budget_set_name(
    message: types.Message, state: FSMContext, filtered_budget_name: str | None
):
    if filtered_budget_name is None:
        await message.answer(
            "Полученное название содержит недопустимые символы или превышает "
            "предельно допустимую длину.\n"
            "В названии бюджета можно использовать только буквы, цифры, "
            "сиволы пробела, тире и нижнего подчеркивания.\n"
            "Вам необходимо уложиться в 25 символов.",
            reply_markup=keyboards.button_menu(keyboards.buttons.main_menu),
        )
        return

    await state.update_data(name=filtered_budget_name)
    await message.answer(
        f"Отлично! Имя Вашего нового бюджета: `{filtered_budget_name}`."
        "\nДалее введите наименование валюты.\n"
        "Наименование должно содержать от 3-х до 10-ти букв "
        "(в любом регистре). Цифры и иные символы не допускаются.\n"
        "Отдавайте предпочтение общепринятым сокращениям, например RUB или USD."
    )
    await state.set_state(BudgetCreatetState.currency)


@router.message(BudgetCreatetState.currency, BudgetCurrencyFilter())
async def create_budget_set_currency_and_finish(
    message: types.Message,
    state: FSMContext,
    user: User,
    db_session: Session | scoped_session,
    filtered_budget_currency: str | None,
):
    if filtered_budget_currency is None:
        await message.answer(
            "Неверный формат обозначения валюты!\n"
            "Наименование должно содержать от 3-х до 10-ти букв "
            "(в любом регистре). Цифры и иные символы не допускаются.\n"
            "Отдавайте предпочтение общепринятым сокращениям, например "
            "RUB или USD.",
            reply_markup=keyboards.button_menu(keyboards.buttons.main_menu),
        )
        return

    created = create_budget(
        db_session,
        user_id=user.id,
        name=f"user{user.tg_id}_{filtered_budget_currency}",
        currency=filtered_budget_currency,
    )

    if created:
        await message.answer(
            "Поздравляем! Вы успешно создали новый личный бюджет.\n"
            f"Название бюджета: {created.name}, валюта: {created.currency}.\n"
            "Можете добавить новые транзакции или категории."
        )

    else:
        await message.answer(
            "Что-то пошло не так при создании нового бюджета.\n"
            "Обратитесь в поддержку."
        )
    await state.clear()


@router.callback_query(F.data == "budget_create")
async def budget_create(callback: types.CallbackQuery, state: FSMContext):
    await cmd_create_budget(callback.message, state)
    await callback.answer()


@router.message(Command("show_budgets"))
async def cmd_show_budgets(
    message: types.Message,
    state: FSMContext,
    user: User,
    db_session: Session | scoped_session,
):
    if count_user_budgets(db_session, user.id) == 0:
        await cmd_create_budget(message, state)
    else:
        budgets = get_user_budgets(db_session, user.id)
        await message.answer(
            "Кликните на нужный бюджет, чтобы выбрать действие",
            reply_markup=keyboards.budget_item_list_interactive(budgets),
        )


@router.callback_query(F.data == "budget_menu")
async def show_budgets(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    db_session: Session | scoped_session,
):
    await cmd_show_budgets(callback.message, state, user, db_session)
    await callback.answer()


@router.callback_query(F.data.startswith("budget_item"))
async def budget_item_show_options(callback: types.CallbackQuery):
    budget_id = callback.data.rsplit("_", maxsplit=1)[-1]
    await callback.message.answer(
        "Выберите действие",
        reply_markup=keyboards.budget_item_choose_action(budget_id),
    )
    await callback.answer()


@router.callback_query(
    BudgetItemActionData.filter(F.action == "delete"),
)
async def budget_item_delete(
    callback: types.CallbackQuery,
    callback_data: BudgetItemActionData,
    db_session: Session | scoped_session,
):
    deleted = delete_budget(db_session, callback_data.budget_id)
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
    db_session: Session | scoped_session,
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
    updated = update_budget(db_session, budget_id, {"currency": currency})
    if updated:
        await message.answer("Бюджет был успешно обновлен")
    else:
        await message.answer(
            "Ошибка обновления бюджета. Бюджет отсутствует или был удален ранее."
        )
    await state.clear()

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from app.bot import keyboards
from app.bot.callback_data import BudgetItemActionData
from app.bot.filters import (
    BudgetCurrencyFilter,
    BudgetNameFilter,
    ExtractBudgetIdFilter,
)
from app.bot.middlewares import AddBudgetControllerMiddleWare
from app.bot.states import (
    BudgetCreateState,
    BudgetShowState,
    BudgetUpdateState,
)
from app.db.models import User
from app.db.queries.core import budget_controller
from app.utils import OffsetPaginator

router = Router()
router.message.middleware(AddBudgetControllerMiddleWare())
router.callback_query.middleware(AddBudgetControllerMiddleWare())


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

    await state.set_state(BudgetCreateState.set_name)


@router.message(BudgetCreateState.set_name, BudgetNameFilter())
async def create_budget_set_name(
    message: types.Message,
    state: FSMContext,
    filtered_budget_name: str | None,
    user: User,
    budget_controller: budget_controller,
):
    if filtered_budget_name is None:
        await message.answer(
            "Полученное название содержит недопустимые символы или превышает "
            "предельно допустимую длину.\n"
            "В названии бюджета можно использовать только буквы, цифры, "
            "сиволы пробела, тире и нижнего подчеркивания.\n"
            "Вам необходимо уложиться в 25 символов.",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.cancel_operation
            ),
        )
        return

    elif budget_controller.budget_exists(
        budget_name=f"user_{user.id}:{filtered_budget_name}"
    ):
        await message.answer(
            f"У Вас уже есть бюджет с названием {filtered_budget_name}.\n"
            "Пожалуйста, придумайте новое название.",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.cancel_operation
            ),
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
    await state.set_state(BudgetCreateState.set_currency)


@router.message(BudgetCreateState.set_currency, BudgetCurrencyFilter())
async def create_budget_set_currency_and_finish(
    message: types.Message,
    state: FSMContext,
    user: User,
    filtered_budget_currency: str | None,
    budget_controller: budget_controller,
):
    if filtered_budget_currency is None:
        await message.answer(
            "Неверный формат обозначения валюты!\n"
            "Наименование должно содержать от 3-х до 10-ти букв "
            "(в любом регистре). Цифры и иные символы не допускаются.\n"
            "Отдавайте предпочтение общепринятым сокращениям, например "
            "RUB или USD.",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.cancel_operation
            ),
        )
        return

    data = await state.get_data()
    budget_name = data["name"]

    created = budget_controller.create_budget(
        user_id=user.id,
        name=budget_name,
        currency=filtered_budget_currency,
    )

    if created is not None:
        await message.answer(
            "Поздравляем! Вы успешно создали новый личный бюджет.\n"
            f"Название бюджета: {created.public_name}, валюта: {created.currency}.\n"
            "Можете добавить новые транзакции или категории.",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.main_menu,
                keyboards.buttons.create_new_entry,
                keyboards.buttons.create_new_category,
            ),
        )

    else:
        await message.answer(
            "Что-то пошло не так при создании нового бюджета.\n"
            "Обратитесь в поддержку."
        )
    await state.clear()


@router.callback_query(F.data == "create_budget")
async def create_budget(callback: types.CallbackQuery, state: FSMContext):
    await cmd_create_budget(callback.message, state)
    await callback.answer()


@router.message(Command("show_budgets"))
async def cmd_show_budgets(
    message: types.Message,
    state: FSMContext,
    user: User,
    budget_controller: budget_controller,
):
    num_budgets = budget_controller.count_user_budgets(user.id)
    if num_budgets == 0:
        # if not budget_controller.budget_exists(user_id=user.id):
        await message.answer(
            "У Вас пока нет ни одного бюджета.\n"
            "Создайте бюджет, нажав на кнопку ниже.",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.create_new_budget,
                keyboards.buttons.main_menu,
            ),
        )
    else:
        budgets = budget_controller.get_user_budgets(user.id)
        paginator = OffsetPaginator("show_budgets_page", num_budgets, 5)
        await message.answer(
            "Кликните на нужный бюджет, чтобы выбрать действие",
            reply_markup=keyboards.paginated_budget_item_list(
                budgets, paginator
            ),
        )
        await state.update_data(paginator=paginator)
        await state.set_state(BudgetShowState.show_budgets)


@router.callback_query(
    BudgetShowState.show_budgets, F.data.startswith("show_budgets_page")
)
async def show_budgets_page(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    budget_controller: budget_controller,
):
    *_, switch_to = callback.data.rsplit("_", maxsplit=1)
    state_data = await state.get_data()
    pagiantor = state_data.get("paginator")

    pagiantor.switch_next() if switch_to == "next" else pagiantor.switch_back()

    budgets = budget_controller.get_user_budgets(
        user.id, pagiantor.current_offset
    )
    await callback.message.answer(
        "Кликните на нужный бюджет, чтобы выбрать действие",
        reply_markup=keyboards.paginated_budget_item_list(budgets, pagiantor),
    )
    await state.update_data(pagiantor=pagiantor)
    await state.set_state(BudgetShowState.show_budgets)


@router.callback_query(F.data == "show_budgets")
async def show_budgets(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    budget_controller: budget_controller,
):
    await cmd_show_budgets(callback.message, state, user, budget_controller)
    await callback.answer()


@router.callback_query(ExtractBudgetIdFilter())
async def budget_item_show_options(
    callback: types.CallbackQuery, extracted_budget_id: int | None
):
    if extracted_budget_id is None:
        await callback.message.answer(
            "Неверный тип данных идентификатора бюджета.\n"
            "Обратитесль в поддержку."
        )

    await callback.message.answer(
        "Выберите действие",
        reply_markup=keyboards.budget_item_choose_action(extracted_budget_id),
    )
    await callback.answer()


@router.callback_query(
    BudgetItemActionData.filter(F.action == "delete"),
)
async def budget_delete(
    callback: types.CallbackQuery,
    callback_data: BudgetItemActionData,
    state: FSMContext,
    budget_controller: budget_controller,
):
    await state.clear()
    deleted = budget_controller.delete_budget(callback_data.budget_id)
    if deleted:
        await callback.message.answer("Бюджет был успешно удален")
    else:
        await callback.message.answer(
            "Ошибка удаления бюджета. Бюджет отсутствует или был удален ранее."
        )
    await callback.answer()


@router.callback_query(BudgetItemActionData.filter(F.action == "update"))
async def update_budget_choose_attribute(
    callback: types.CallbackQuery,
    callback_data: BudgetItemActionData,
    state: FSMContext,
):
    await callback.message.answer(
        "Желаете изменить ваш бюджет?\n"
        "Выберите параметр, который необходимо изменить.",
        reply_markup=keyboards.create_callback_buttons(
            button_names={
                "название": "name",
                "валюта": "currency",
                "завершить": "finish",
            },
            callback_prefix="update_budget",
        ),
    )

    await state.set_state(BudgetUpdateState.choose_attribute)
    await state.set_data({"budget_id": callback_data.budget_id})
    await callback.answer()


@router.callback_query(
    BudgetUpdateState.choose_attribute, F.data == "update_budget_name"
)
async def update_budget_provide_name(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    await callback.message.answer("Введите новое название бюджета.")
    await state.set_state(BudgetUpdateState.update_name)
    await callback.answer()


@router.message(
    BudgetUpdateState.update_name,
    BudgetNameFilter(),
)
async def update_budget_set_name(
    message: types.Message,
    state: FSMContext,
    user: User,
    filtered_budget_name: str | None,
    budget_controller: budget_controller,
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

    elif budget_controller.budget_exists(
        budget_name=f"user_{user.id}:{filtered_budget_name}"
    ):
        await message.answer(
            f"У вас уже есть бюджет с названием {filtered_budget_name}"
        )
        return

    else:
        await state.update_data(name=filtered_budget_name)

    await message.answer(
        f"Вы поменяли название бюджета на `{filtered_budget_name}`.\n"
        "Вы можете изменить остальные параметры бюджета "
        "или завершить редактирование.",
        reply_markup=keyboards.create_callback_buttons(
            button_names={
                "название": "name",
                "валюта": "currency",
                "завершить": "finish",
            },
            callback_prefix="update_budget",
        ),
    )
    await state.set_state(BudgetUpdateState.choose_attribute)


@router.callback_query(
    BudgetUpdateState.choose_attribute, F.data == "update_budget_currency"
)
async def update_budget_provide_currency(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    await callback.message.answer("Введите новую валюту бюджета.")
    await state.set_state(BudgetUpdateState.update_currency)
    await callback.answer()


@router.message(
    BudgetUpdateState.update_currency,
    BudgetCurrencyFilter(),
)
async def update_budget_set_currency(
    message: types.Message,
    state: FSMContext,
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

    else:
        await state.update_data(currency=filtered_budget_currency)

    await message.answer(
        f"Вы поменяли валюту бюджета на `{filtered_budget_currency}`.\n"
        "Вы можете изменить остальные параметры бюджета "
        "или завершить редактирование.",
        reply_markup=keyboards.create_callback_buttons(
            button_names={
                "название": "name",
                "валюта": "currency",
                "завершить": "finish",
            },
            callback_prefix="update_budget",
        ),
    )
    await state.set_state(BudgetUpdateState.choose_attribute)


@router.callback_query(
    BudgetUpdateState.choose_attribute, F.data == "update_budget_finish"
)
async def update_budget_finish(
    callback: types.CallbackQuery,
    state: FSMContext,
    budget_controller: budget_controller,
):
    user_data = await state.get_data()
    budget_id = user_data.pop("budget_id")

    updated = budget_controller.update_budget(budget_id, user_data)
    if updated:
        await callback.message.answer("Бюджет был успешно обновлен.")
    else:
        await callback.message.answer(
            "Ошибка обновления бюджета. Бюджет отсутствует или был удален ранее."
        )
    await state.clear()

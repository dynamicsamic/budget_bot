import logging

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from app.bot import keyboards, prompts
from app.bot.callback_data import CategoryItemActionData
from app.bot.filters import (
    CategoryIdFIlter,
    CategoryNameFilter,
    CategoryTypeFilter,
    SelectPaginatorPageFilter,
)
from app.bot.middlewares import CategoryRepositoryMiddleWare
from app.bot.states import CreateCategory, ShowCategories, UpdateCategory
from app.db.models import CategoryType, User
from app.db.repository import CategoryRepository
from app.utils import OffsetPaginator, aiogram_log_handler

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)


router = Router()

router.message.middleware(CategoryRepositoryMiddleWare())
router.callback_query.middleware(CategoryRepositoryMiddleWare())


@router.message(Command("create_category"))
async def cmd_create_category(
    message: types.Message,
    state: FSMContext,
):
    await message.answer(
        "Введите название новой категории.\n"
        f"{prompts.category_name_description}",
        reply_markup=keyboards.button_menu(
            keyboards.buttons.cancel_operation, keyboards.buttons.main_menu
        ),
    )
    await state.set_state(CreateCategory.set_name)
    logger.info("SUCCESS")


@router.message(CreateCategory.set_name, CategoryNameFilter())
async def create_category_set_name(
    message: types.Message,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
    filtered_category_name: str | None,
    error_message: str | None,
):
    if filtered_category_name is None:
        await message.answer(error_message)
        return

    elif repository.category_exists(
        user_id=user.id, category_name=filtered_category_name
    ):
        await message.answer(
            "У Вас уже есть категория с названием "
            f"{filtered_category_name.capitalize()}.\n"
            "Пожалуйста, придумайте другое название для новой категории.",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.cancel_operation
            ),
        )
        return

    await state.update_data(category_name=filtered_category_name)
    await message.answer(
        "Выберите один из двух типов категорий",
        reply_markup=keyboards.create_callback_buttons(
            button_names={"Доходы": "income", "Расходы": "expenses"},
            callback_prefix="select_category_type",
        ),
    )
    await state.set_state(CreateCategory.set_type)


@router.callback_query(CreateCategory.set_type, CategoryTypeFilter())
async def create_category_set_type_and_finish(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
    category_type: CategoryType,
):
    user_data = await state.get_data()
    category_name = user_data["category_name"]

    created, error = repository.create_category(
        user_id=user.id,
        name=category_name,
        type=category_type,
    ).astuple()

    if error is None:
        await callback.message.answer(
            f"Вы успешно создали новую категорию: {created.render()}",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.show_categories, keyboards.buttons.main_menu
            ),
        )
    else:
        await callback.message.answer(
            # add error handler
            prompts.create_failure_contact_support.format(
                instance_name="категории"
            )
        )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "create_category")
async def category_create(callback: types.CallbackQuery, state: FSMContext):
    await cmd_create_category(callback.message, state)
    await callback.answer()


@router.message(Command("show_categories"))
async def cmd_show_categories(
    message: types.Message,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
):
    categories = repository.get_user_categories(user.id)
    if categories.is_empty:
        await message.answer(
            "У вас пока нет созданных категорий.\n"
            "Создайте категорию, нажав на кнопку ниже.",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.create_new_category,
                keyboards.buttons.main_menu,
            ),
        )
    else:
        category_count = repository.count_user_categories(user.id)
        paginator = OffsetPaginator("category_page_num", category_count, 5)
        await message.answer(
            prompts.category_choose_action,
            reply_markup=keyboards.paginated_category_item_list(
                categories.result, paginator
            ),
        )
        await state.update_data(paginator=paginator)
        await state.set_state(ShowCategories.show_many)


@router.callback_query(ShowCategories.show_many, SelectPaginatorPageFilter())
async def show_categories_page(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
    switch_to_page: str,
):
    state_data = await state.get_data()
    paginator = state_data.get("paginator")

    paginator.switch_next() if switch_to_page == "next" else paginator.switch_back()

    categories = repository.get_user_categories(
        user.id, offset=paginator.current_offset
    )
    await callback.message.answer(
        prompts.category_choose_action,
        reply_markup=keyboards.paginated_category_item_list(
            categories.result, paginator
        ),
    )
    await state.update_data(paginator=paginator)
    await state.set_state(ShowCategories.show_many)


@router.callback_query(F.data == "show_categories")
async def show_categories(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
):
    await cmd_show_categories(callback.message, state, user, repository)
    await callback.answer()


@router.callback_query(ShowCategories.show_many, CategoryIdFIlter())
async def show_category_options(
    callback: types.CallbackQuery, state: FSMContext, category_id: int
):
    await callback.message.answer(
        "Выберите действие",
        reply_markup=keyboards.category_item_choose_action(category_id),
    )
    await state.set_state(ShowCategories.show_one)
    await callback.answer()


@router.callback_query(
    ShowCategories.show_one,
    CategoryItemActionData.filter(F.action == "delete"),
)
async def delete_category(
    callback: types.CallbackQuery,
    state: FSMContext,
    callback_data: CategoryItemActionData,
    repository: CategoryRepository,
):
    deleted, error = repository.delete_category(
        callback_data.category_id
    ).astuple()
    if deleted:
        await callback.message.answer(
            "Категория была успешно удалена",
            reply_markup=keyboards.show_categories_and_main_menu(),
        )
    else:
        # add error handler
        await callback.message.answer(
            "Ошибка удаления категории. Категория отсутствует или была удалена ранее."
        )

    await state.clear()
    await callback.answer()


@router.callback_query(
    ShowCategories.show_one,
    CategoryItemActionData.filter(F.action == "update"),
)
async def update_category_get_name(
    callback: types.CallbackQuery,
    callback_data: CategoryItemActionData,
    state: FSMContext,
):
    await state.clear()  # clear show state to start update state
    await state.set_data({"category_id": callback_data.category_id})
    await callback.message.answer(
        "Введите новое название категории (не должно быть длинее 128 символов)"
    )

    await state.set_state(UpdateCategory.name)
    await callback.answer()


@router.message(
    UpdateCategory.name,
    CategoryNameFilter(),
)
async def update_category_get_type(
    message: types.Message,
    state: FSMContext,
    category_name: str,
    error_message: str,
    repository: CategoryRepository,
):
    if not category_name:
        await message.answer(error_message)
        return

    data = await state.get_data()
    category_id = data["category_id"]
    updated, error = repository.update_category(
        category_id, {"name": "category_name"}
    ).astuple()

    if updated:
        await message.answer(
            f"Название категории было изменено на: {category_name}",
            reply_markup=keyboards.show_categories_and_main_menu(),
        )
    else:
        # add error handler
        await message.answer(
            "Ошибка обновления категории. Категория отсутствует или была удалена ранее."
        )
    await state.clear()
    await state.clear()

import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.bot import keyboards, prompts
from app.bot.callback_data import (
    CategoryItemActionData,
    UpdateCategoryChooseAttribute,
)
from app.bot.filters import (
    CategoryDeleteConfirmFilter,
    CategoryIdFIlter,
    CategoryNameFilter,
    CategoryTypeFilter,
    SelectCategoryPageFilter,
)
from app.bot.middlewares import CategoryRepositoryMiddleWare
from app.bot.states import CreateCategory, ShowCategories, UpdateCategory
from app.db.models import CategoryType, User
from app.db.repository import CategoryRepository
from app.exceptions import ModelInstanceDuplicateAttempt
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


@router.message(CreateCategory.set_name, CategoryNameFilter)
async def create_category_set_name(
    message: types.Message,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
    category_name: str,
):
    if repository.category_exists(
        user_id=user.id, category_name=category_name
    ):
        raise ModelInstanceDuplicateAttempt(
            user_tg_id=user.tg_id,
            model_name="Категория",
            duplicate_arg_name="Название",
            duplicate_arg_value=category_name,
        )

    await message.answer(
        "Выберите один из двух типов категорий",
        reply_markup=keyboards.create_callback_buttons(
            button_names={"Доходы": "income", "Расходы": "expenses"},
            callback_prefix="select_category_type",
        ),
    )

    await state.update_data(category_name=category_name)
    await state.set_state(CreateCategory.set_type)
    logger.info("SUCCESS")


@router.callback_query(
    CreateCategory.set_type,
    CategoryTypeFilter,
)
async def create_category_set_type_and_finish(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
    category_type: CategoryType,
):
    user_data = await state.get_data()
    category_name = user_data["category_name"]

    created = repository.create_category(
        user_id=user.id,
        name=category_name,
        type=category_type,
    )

    await callback.message.answer(
        f"Вы успешно создали новую категорию: {created.render()}",
        reply_markup=keyboards.button_menu(
            keyboards.buttons.show_categories, keyboards.buttons.main_menu
        ),
    )
    await state.clear()
    await callback.answer()
    logger.info(f"SUCCESS, created new category: {created.render()}")


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
        logger.info(
            "FAILURE, no categories to show, redirect to create_category"
        )

    else:
        category_count = repository.count_user_categories(user.id)
        paginator = OffsetPaginator("show_categories_page", category_count, 5)
        await message.answer(
            prompts.category_choose_action,
            reply_markup=keyboards.paginated_category_item_list(
                categories.result, paginator
            ),
        )
        await state.update_data(paginator=paginator)
        await state.set_state(ShowCategories.show_many)
        logger.info(f"SUCCESS, show first {paginator.page_limit} categories")


@router.callback_query(ShowCategories.show_many, SelectCategoryPageFilter)
async def show_categories_page(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
    switch_to_page: str,
):
    state_data = await state.get_data()
    paginator = state_data.get("paginator")

    (
        paginator.switch_next()
        if switch_to_page == "next"
        else paginator.switch_back()
    )

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
    logger.info(
        f"SUCCESS, show {paginator.page_limit} categories "
        f"starting from {paginator.current_offset + 1}"
    )


@router.callback_query(F.data == "show_categories")
async def show_categories(
    callback: types.CallbackQuery,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
):
    await cmd_show_categories(callback.message, state, user, repository)
    await callback.answer()


@router.callback_query(ShowCategories.show_many, CategoryIdFIlter)
async def show_category_control_options(
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
async def delete_category_warn_user(
    callback: types.CallbackQuery,
    callback_data: CategoryItemActionData,
    repository: CategoryRepository,
):
    category_id = callback_data.category_id
    category = repository.get_category(category_id)
    entry_count = repository.count_category_entries(category_id)

    await callback.message.answer(
        prompts.show_delete_category_warning(category.name, entry_count),
        reply_markup=keyboards.button_menu(
            keyboards.buttons.switch_to_update_category(category_id),
            keyboards.buttons.confirm_delete_category(category_id),
        ),
    )
    await callback.answer()
    logger.info("SUCCESS")


@router.callback_query(
    ShowCategories.show_one,
    CategoryDeleteConfirmFilter,
)
async def delete_category_confirm(
    callback: types.CallbackQuery,
    state: FSMContext,
    repository: CategoryRepository,
    category_id: int,
):
    repository.delete_category(category_id)
    await callback.message.answer(
        prompts.confirm_category_deleted,
        reply_markup=keyboards.button_menu(
            keyboards.buttons.show_categories, keyboards.buttons.main_menu
        ),
    )
    logger.info(f"SUCCESS, category id {category_id} deleted")

    await state.clear()
    await callback.answer()


@router.callback_query(
    ShowCategories.show_one,
    CategoryItemActionData.filter(F.action == "update"),
)
async def update_category_choose_attribute(
    callback: types.CallbackQuery,
    callback_data: CategoryItemActionData,
    state: FSMContext,
):
    await state.clear()  # clear show state to start update state

    await callback.message.answer(
        prompts.update_category_invite_user,
        reply_markup=keyboards.create_callback_buttons(
            button_names={
                "название": "name",
                "тип": "type",
                "завершить": "finish",
            },
            callback_prefix="update_category",
        ),
    )

    await state.set_state(UpdateCategory.choose_attribute)
    await state.set_data({"category_id": callback_data.category_id})
    await callback.answer()


@router.callback_query(
    UpdateCategory.choose_attribute,
    UpdateCategoryChooseAttribute.filter(F.attribute == "name"),
)
async def update_category_request_name(
    callback: types.CallbackQuery, state: FSMContext
):
    await callback.message.answer(
        "Введите новое название категории"
        f"{prompts.category_name_description}",
        reply_markup=keyboards.button_menu(
            keyboards.buttons.cancel_operation, keyboards.buttons.main_menu
        ),
    )
    await state.set_state(UpdateCategory.update_name)


@router.message(UpdateCategory.update_name, CategoryNameFilter)
async def update_category_set_name(
    message: types.Message,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
    category_name: str,
):
    if repository.category_exists(
        user_id=user.id, category_name=category_name
    ):
        raise ModelInstanceDuplicateAttempt(
            user_tg_id=user.tg_id,
            model_name="Категория",
            duplicate_arg_name="Название",
            duplicate_arg_value=category_name,
        )

    await message.answer(
        prompts.update_category_confirm_new_name.format(
            category_name=category_name
        ),
        reply_markup=keyboards.create_callback_buttons(
            button_names={
                "название": "name",
                "тип": "type",
                "завершить": "finish",
            },
            callback_prefix="update_category",
        ),
    )
    await state.update_data(category_name=category_name)
    await state.set_state(UpdateCategory.choose_attribute)


@router.message(
    UpdateCategory.choose_attribute,
    CategoryNameFilter,
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

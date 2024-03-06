import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot import string_constants as sc
from app.bot.filters import (
    CategoryDeleteConfirmFilter,
    CategoryIdFIlter,
    CategoryItemActionData,
    CategoryNameFilter,
    CategoryTypeFilter,
    SelectCategoryPageFilter,
    UpdateCategoryChooseAttrData,
)
from app.bot.middlewares import CategoryRepositoryMiddleWare
from app.bot.states import CreateCategory, ShowCategories, UpdateCategory
from app.bot.templates import buttons, const, func, texts
from app.bot.templates.base import button_menu, create_callback_buttons
from app.bot.templates.keyboards import (
    category_update_options,
    delete_category_warning,
    show_categories_menu,
)
from app.db.models import CategoryType, User
from app.db.repository import CategoryRepository
from app.exceptions import ModelInstanceDuplicateAttempt
from app.utils import OffsetPaginator, aiogram_log_handler

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)


router = Router()

router.message.middleware(CategoryRepositoryMiddleWare)
router.callback_query.middleware(CategoryRepositoryMiddleWare)


@router.message(Command(sc.CREATE_CATEGORY_COMMAND))
async def cmd_create_category(message: Message, state: FSMContext):
    await state.set_state(CreateCategory.set_name)
    await message.answer(**const.category_name_description)
    logger.info(f"user id={message.from_user.id} started new category process")


@router.message(CreateCategory.set_name, CategoryNameFilter)
async def create_category_set_name(
    message: Message,
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

    await state.set_state(CreateCategory.set_type)
    await state.update_data(category_name=category_name)
    await message.answer(**const.category_type_selection)
    logger.info(
        f"name `{category_name}` recieved "
        f"for user id={message.from_user.id} new category"
    )


@router.callback_query(
    CreateCategory.set_type,
    CategoryTypeFilter,
)
async def create_category_set_type_and_finish(
    callback: CallbackQuery,
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

    await state.clear()
    await callback.message.answer(**func.show_category_create_summary(created))
    await callback.answer()
    logger.info(
        f"user id={callback.from_user.id} created new category: {created}"
    )


@router.message(Command(sc.SHOW_CATEGORIES_COMMAND))
async def cmd_show_categories(
    message: Message,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
):
    categories = repository.get_user_categories(user.id)
    if categories.is_empty:
        await message.answer(**const.zero_category)
        logger.info(
            f"user id={message.from_user.id} has no categories yet; "
            "redirect to create_category"
        )

    else:
        category_count = repository.count_user_categories(user.id)
        paginator = OffsetPaginator(
            sc.PAGINATED_CATEGORIES_PAGE, category_count, 5
        )
        await state.set_state(ShowCategories.show_many)
        await state.update_data(paginator=paginator)
        await message.answer(
            **func.show_paginated_categories(categories.result, paginator)
        )
        logger.info(
            f"user id={message.from_user.id} GET "
            f"first {paginator.page_limit} categories"
        )


@router.callback_query(ShowCategories.show_many, SelectCategoryPageFilter)
async def show_categories_page(
    callback: CallbackQuery,
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
    await state.update_data(paginator=paginator)
    await callback.message.answer(
        **func.show_paginated_categories(categories, paginator)
    )
    logger.info(
        f"user id={callback.from_user.id} GET {paginator.page_limit} "
        f"categories starting from {paginator.current_offset + 1}"
    )


@router.callback_query(ShowCategories.show_many, CategoryIdFIlter)
async def show_category_control_options(
    callback: CallbackQuery, state: FSMContext, category_id: int
):
    await state.clear()  # remove paginator from state data
    await callback.message.answer(
        **func.show_category_control_options(category_id)
    )
    await state.set_state(ShowCategories.show_one)
    await callback.answer()
    logger.info(
        f"user id={callback.from_user.id} GET update or delete category select"
    )


@router.callback_query(
    ShowCategories.show_one,
    CategoryItemActionData.filter(F.action == "delete"),
)
async def delete_category_warn_user(
    callback: CallbackQuery,
    callback_data: CategoryItemActionData,
    repository: CategoryRepository,
):
    category_id = callback_data.category_id
    category = repository.get_category(category_id)
    entry_count = repository.count_category_entries(category_id)

    await callback.message.answer(
        texts.show_delete_category_warning(category.name, entry_count),
        reply_markup=delete_category_warning(category_id),
    )
    logger.info("SUCCESS")
    await callback.answer()


@router.callback_query(
    ShowCategories.show_one,
    CategoryDeleteConfirmFilter,
)
async def delete_category_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    repository: CategoryRepository,
    category_id: int,
):
    repository.delete_category(category_id)
    await callback.message.answer(
        texts.confirm_category_deleted,
        reply_markup=show_categories_menu,
    )

    await state.clear()
    logger.info(f"SUCCESS, category id {category_id} deleted")
    await callback.answer()


@router.callback_query(
    ShowCategories.show_one,
    CategoryItemActionData.filter(F.action == "update"),
)
async def update_category_choose_attribute(
    callback: CallbackQuery,
    callback_data: CategoryItemActionData,
    state: FSMContext,
):
    await state.clear()  # clear show state to start update state

    await callback.message.answer(
        texts.update_category_invite_user,
        reply_markup=category_update_options,
    )

    await state.set_state(UpdateCategory.choose_attribute)
    await state.set_data({"category_id": callback_data.category_id})
    logger.info("SUCCESS")
    await callback.answer()


@router.callback_query(
    UpdateCategory.choose_attribute,
    UpdateCategoryChooseAttrData.filter(F.attribute == "name"),
)
async def update_category_request_name(
    callback: CallbackQuery, state: FSMContext
):
    await callback.message.answer(**const.category_name_description)
    await state.set_state(UpdateCategory.update_name)
    logger.info("SUCCESS")
    await callback.answer()


@router.message(UpdateCategory.update_name, CategoryNameFilter)
async def update_category_set_name(
    message: Message,
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

    state_data = await state.get_data()
    category_id = state_data.get("category_id")
    repository.update_category(category_id, name=category_name)

    await message.answer(
        texts.update_category_confirm_new_name.format(
            category_name=category_name
        ),
        reply_markup=category_update_options,
    )
    await state.update_data(category_name=category_name)
    await state.set_state(UpdateCategory.choose_attribute)
    logger.info(
        f"SUCCESS, category id {category_id} name updated to {category_name}"
    )


@router.callback_query(
    UpdateCategory.choose_attribute,
    UpdateCategoryChooseAttrData.filter(F.attribute == "type"),
)
async def update_category_request_type(
    callback: CallbackQuery, state: FSMContext
):
    await callback.message.answer(
        "Выберите новый тип категории",
        reply_markup=create_callback_buttons(
            button_names={"Доходы": "income", "Расходы": "expenses"},
            callback_prefix=sc.SELECT_CATEGORY_TYPE,
        ),
    )
    await state.set_state(UpdateCategory.update_type)
    logger.info("SUCCESS")
    await callback.answer()


@router.callback_query(UpdateCategory.update_type, CategoryTypeFilter)
async def update_category_set_type(
    callback: CallbackQuery,
    state: FSMContext,
    repository: CategoryRepository,
    category_type: CategoryType,
):
    state_data = await state.get_data()
    category_id = state_data.get("category_id")
    repository.update_category(category_id, type=category_type)

    await callback.message.answer(
        texts.update_category_confirm_new_type.format(
            category_type=category_type.description
        ),
        reply_markup=category_update_options,
    )
    await state.update_data(category_type=category_type)
    await state.set_state(UpdateCategory.choose_attribute)
    logger.info(
        f"SUCCESS, category id {category_id} type updated to {category_type.value}"
    )
    await callback.answer()


@router.callback_query(
    UpdateCategory.choose_attribute,
    UpdateCategoryChooseAttrData.filter(F.attribute == "finish"),
)
async def update_category_finish(
    callback: CallbackQuery,
    state: FSMContext,
    repository: CategoryRepository,
):
    state_data = await state.get_data()
    category_id = state_data.pop("category_id", None)
    if state_data == {}:
        await callback.message.answer(
            texts.update_without_changes,
            reply_markup=button_menu(
                buttons.show_categories, buttons.main_menu
            ),
        )
        logger.info("Category update finished without changes.")

    else:
        category = repository.get_category(category_id)
        await callback.message.answer(
            texts.show_update_summary(category),
            reply_markup=button_menu(
                buttons.show_categories, buttons.main_menu
            ),
        )
        logger.info(f"SUCCESS, category id {category_id} update finished.")

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == sc.CREATE_CATEGORY_CALL)
async def create_category(callback: CallbackQuery, state: FSMContext):
    await cmd_create_category(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == sc.SHOW_CATEGORIES_CALL)
async def show_categories(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    repository: CategoryRepository,
):
    await cmd_show_categories(callback.message, state, user, repository)
    await callback.answer()

from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext

from app.bot import keyboards
from app.bot.middlewares import DataBaseSessionMiddleWare
from app.db.managers import ModelManager
from app.db.models import EntryType, User

from .states import CategoryCreateState, CategoryUpdateState

router = Router()
router.message.middleware(DataBaseSessionMiddleWare())
router.callback_query.middleware(DataBaseSessionMiddleWare())


@router.message(Command("category_create"))
async def cmd_create_category(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название категории "
        "(название не должно быть длинее 128 символов)."
    )
    await state.set_state(CategoryCreateState.name)


@router.message(CategoryCreateState.name)
async def create_category_request_type(
    message: types.Message,
    state: FSMContext,
):
    name = message.text
    if len(name) > 128:
        await message.answer(
            "Слишком длинное название категории."
            "Придумайте более короткое название."
        )
        return

    await state.update_data(category_name=name)
    await message.answer(
        "Выберите один из двух типов категорий",
        reply_markup=keyboards.choose_category_type(),
    )
    await state.set_state(CategoryCreateState.type)


@router.callback_query(
    CategoryCreateState.type, F.data.startswith("choose_entry_category")
)
async def create_category_finish(
    callback: types.CallbackQuery,
    state: FSMContext,
    model_managers: dict[str, Type[ModelManager]],
    user: User,
):
    *_, type_ = callback.data.rsplit("_", maxsplit=1)
    if type_ == "income":
        category_type = EntryType.INCOME
    elif type_ == "expenses":
        category_type = EntryType.EXPENSES
    else:
        await callback.message.answer(
            "Для продолжения выберите тип категории, "
            "нажав на одну из вышеуказанных кнопок."
        )
        return
    data = await state.get_data()
    category_name = data["category_name"]
    await state.clear()

    categories = model_managers["category"]
    created = categories.create(
        name=category_name,
        type=category_type,
        user_id=user.id,
    )
    if created:
        await callback.message.answer(
            f"Вы успешно создали новую категорию `{category_name}`"
        )
    else:
        await callback.message.answer(
            "Что-то пошло не так при создании категории. Обратитесь в поддержку"
        )
    await callback.answer()


@router.callback_query(Text("category_create"))
async def category_create(callback: types.CallbackQuery, state: FSMContext):
    await cmd_create_category(callback.message, state)
    await callback.answer()


@router.message(Command("show_categories"))
async def cmd_show_categories(
    message: types.Message, user: User, state: FSMContext
):
    categories = user.categories
    if not categories:
        await cmd_create_category(message, state)
    else:
        await message.answer(
            "Кликните на нужную категорию, чтобы выбрать действие",
            reply_markup=keyboards.category_item_list_interactive(categories),
        )


@router.callback_query(Text("category_menu"))
async def show_categories(
    callback: types.CallbackQuery, user: User, state: FSMContext
):
    await cmd_show_categories(callback.message, user, state)
    await callback.answer()


@router.callback_query(F.data.startswith("category_item"))
async def category_item_show_options(callback: types.CallbackQuery):
    category_id = callback.data.rsplit("_", maxsplit=1)[-1]
    await callback.message.answer(
        "Выберите действие",
        reply_markup=keyboards.category_item_choose_action(category_id),
    )
    await callback.answer()

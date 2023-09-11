from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext

from app.bot import keyboards
from app.bot.middlewares import DataBaseSessionMiddleWare
from app.db.managers import ModelManager
from app.db.models import EntryType, User

from .callback_data import categoryItemActionData
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


@router.message(CategoryCreateState.type, F.text.in_(["Доходы, Расходы"]))
async def create_category_finish(
    message: types.Message,
    state: FSMContext,
    model_managers: dict[str, Type[ModelManager]],
    user: User,
):
    type_ = message.text
    if type_ == "Доходы":
        category_type = EntryType.INCOME
    elif type_ == "Расходы":
        category_type = EntryType.EXPENSES
    await state.clear()
    data = await state.get_data()

    categories = model_managers["category"]
    created = categories.create(
        name=data["category_name"],
        type=category_type,
        user_id=user.id,
    )
    if created:
        await message.answer(
            f"Вы успешно создали новую категорию `{data['category_name']}`"
        )
    else:
        await message.answer(
            "Что-то пошло не так при создании категории. Обратитесь в поддержку"
        )

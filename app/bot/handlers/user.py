import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot import string_constants as sc
from app.bot.filters import (
    BudgetCurrencyFilter,
    CurrencyUpdateData,
    UserSignupData,
)
from app.bot.middlewares import UserRepositoryMiddleWare
from app.bot.states import CreateUser, UpdateUser
from app.bot.templates import const, func
from app.db.models import User
from app.db.repository import UserRepository
from app.utils import aiogram_log_handler

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)

router = Router()
router.callback_query.middleware(UserRepositoryMiddleWare)


@router.callback_query(
    CreateUser.choose_signup_type,
    UserSignupData.filter(F.action == "start"),
    flags={"allow_anonymous": True},
)
async def choose_signup_type(
    callback: CallbackQuery,
    state: FSMContext,
):
    tg_id = callback.from_user.id
    await state.update_data(tg_id=tg_id)
    await callback.message.answer(**const.choose_signup_type)
    await callback.answer()
    logger.info(f"start signup for user id={tg_id}")


@router.callback_query(
    CreateUser.choose_signup_type,
    UserSignupData.filter(F.action == "advanced"),
    flags={"allow_anonymous": True},
)
async def start_advanced_signup(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateUser.advanced_signup)
    await callback.message.answer(**const.advanced_signup_menu)
    await callback.answer()
    logger.info(f"user id={callback.from_user.id} chose advanced signup.")


@router.callback_query(
    CreateUser.advanced_signup,
    UserSignupData.filter(F.action == "get_currency"),
    flags={"allow_anonymous": True},
)
async def request_currency(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateUser.get_budget_currency)
    await callback.message.answer(**const.budget_currency_description)
    await callback.answer()
    logger.info(
        f"waiting for currency from new user id={callback.from_user.id}."
    )


@router.message(
    CreateUser.get_budget_currency,
    BudgetCurrencyFilter,
    flags={"allow_anonymous": True},
)
async def set_currency(
    message: Message, state: FSMContext, budget_currency: str
):
    await state.set_state(CreateUser.choose_signup_type)
    await state.update_data(budget_currency=budget_currency)
    await message.answer(**func.show_signup_currency(budget_currency))
    logger.info(
        f"new user id={message.from_user.id} "
        f"submitted valid currency: {budget_currency}."
    )


@router.callback_query(
    CreateUser.choose_signup_type,
    UserSignupData.filter(F.action == "basic"),
    flags={"allow_anonymous": True},
)
async def finish_signup(
    callback: CallbackQuery,
    state: FSMContext,
    repository: UserRepository,
):
    user_data = await state.get_data()
    tg_id = user_data.get("tg_id")
    budget_currency = user_data.get("budget_currency", "RUB")
    created = repository.create_user(
        tg_id=tg_id, budget_currency=budget_currency
    )
    await callback.message.answer(**func.show_signup_summary(created))

    await state.clear()
    await callback.answer()
    logger.info(f"new user created: {created}")


@router.callback_query(F.data == sc.SHOW_USER_PROFILE)
async def show_user_profile(callback: CallbackQuery):
    await callback.message.answer(**const.user_profile)
    await callback.answer()
    logger.info(f"show profile for user id={callback.from_user.id}")


@router.callback_query(F.data == sc.DELETE_USER)
async def delete_user(
    callback: CallbackQuery, user: User, repository: UserRepository
):
    repository.update_user(user.id, is_active=False)
    await callback.message.answer(**const.user_delete_summary)
    await callback.answer()
    logger.info(f"user id={callback.from_user.id} deactivated")


@router.callback_query(CurrencyUpdateData.filter(F.action == "start"))
async def update_budget_currency(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UpdateUser.budget_currency)
    await callback.message.answer(**const.budget_currency_description)
    await callback.answer()
    logger.info(f"user id={callback.from_user.id} started currency update")


@router.message(UpdateUser.budget_currency, BudgetCurrencyFilter)
async def set_updated_currency(
    message: Message,
    state: FSMContext,
    budget_currency: str,
):
    await state.update_data(budget_currency=budget_currency)
    await message.answer(**func.confirm_updated_currency(budget_currency))
    logger.info(
        f"user id={message.from_user.id} is "
        f"switching budget currency to: {budget_currency}"
    )


@router.callback_query(
    UpdateUser.budget_currency,
    CurrencyUpdateData.filter(F.action == "reset"),
)
async def reset_updated_currency(callback: CallbackQuery, state: FSMContext):
    await state.update_data(budget_currency=None)
    await callback.message.answer(**const.budget_currency_description)
    await callback.answer()
    logger.info(f"user id={callback.from_user.id} resetting currency")


@router.callback_query(
    UpdateUser.budget_currency,
    CurrencyUpdateData.filter(F.action == "confirm"),
)
async def confirm_updated_currency(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    repository: UserRepository,
):
    state_data = await state.get_data()
    budget_currency = state_data.get("budget_currency", "RUB")
    repository.update_user(user.id, budget_currency=budget_currency)
    await callback.message.answer(
        **func.show_currency_update_summary(budget_currency)
    )
    await state.clear()
    await callback.answer()
    logger.info(
        f"user id={callback.from_user.id} "
        f"updated currency: {budget_currency}"
    )


@router.callback_query(
    F.data == sc.ACTIVATE_USER, flags={"allow_anonymous": True}
)
async def activate_user(
    callback: CallbackQuery, user: User, repository: UserRepository
):
    repository.update_user(user.id, is_active=True)
    await callback.message.answer(**const.user_activation_summary)
    await callback.answer()
    logger.info(f"user id={callback.from_user.id} activated")

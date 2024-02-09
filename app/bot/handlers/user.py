import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.callback_data import SignupUserCallbackData
from app.bot.filters import BudgetCurrencyFilter
from app.bot.middlewares import UserRepositoryMiddleWare
from app.bot.replies import prompts
from app.bot.replies.keyboards.common import (
    switch_to_main,
    switch_to_main_or_cancel,
)
from app.bot.replies.keyboards.user import (
    choose_signup_type,
    finish_signup,
    user_activation_menu,
    user_profile_menu,
    user_signup_menu,
)
from app.bot.states import CreateUser
from app.db.models import User
from app.db.repository import UserRepository
from app.utils import aiogram_log_handler

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)

router = Router()
router.callback_query.middleware(UserRepositoryMiddleWare())


@router.callback_query(
    CreateUser.choose_action,
    SignupUserCallbackData.filter(F.action == "start"),
    flags={"allow_anonymous": True},
)
async def signup_user(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    if user.is_active:
        await state.clear()
        await callback.message.answer(
            prompts.signup_active_user,
            reply_markup=switch_to_main_or_cancel,
        )
        logger.info("user is already active; redirect to main menu")
        return

    elif user.is_anonymous:
        tg_id = callback.from_user.id
        await state.update_data(tg_id=tg_id)
        await callback.message.answer(
            prompts.choose_signup_type,
            reply_markup=choose_signup_type,
        )
        logger.info(f"start signup for user tg_id {tg_id}")

    else:
        await state.clear()
        await callback.message.answer(
            prompts.signup_inactive_user,
            reply_markup=user_activation_menu,
        )
        logger.info("user is inactive; redirect to activation menu")
        return

    await callback.answer()


@router.callback_query(
    CreateUser.choose_action,
    SignupUserCallbackData.filter(F.action == "set_currency"),
    flags={"allow_anonymous": True},
)
async def signup_user_request_currency(
    callback: CallbackQuery, state: FSMContext
):
    await state.set_state(CreateUser.set_budget_currency)
    await callback.message.answer(prompts.budget_currency_description)
    await callback.answer()


@router.message(
    CreateUser.set_budget_currency,
    BudgetCurrencyFilter(),
    flags={"allow_anonymous": True},
)
async def signup_user_set_currency(
    message: Message, state: FSMContext, filtered_budget_currency: str | None
):
    if filtered_budget_currency is None:
        await message.answer(
            prompts.invalid_budget_currency_description,
            reply_markup=switch_to_main_or_cancel,
        )
        return

    await state.set_state(CreateUser.choose_action)
    await state.update_data(budget_currency=filtered_budget_currency)
    await message.answer(
        prompts.signup_user_show_currency_and_finish(filtered_budget_currency),
        reply_markup=finish_signup,
    )


@router.callback_query(
    CreateUser.choose_action,
    SignupUserCallbackData.filter(F.action == "finish"),
    flags={"allow_anonymous": True},
)
async def signup_user_finish(
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

    if created is not None:
        await callback.message.answer(
            "Поздравляем! Вы успешно зарегистрированы в системе.\n"
            "Вы можете продложить работу с ботом в главном меню.",
            reply_markup=switch_to_main,
        )

    else:
        await callback.message.answer(
            "Что-то пошло не так при регистрации.\nОбратитесь в поддержку."
        )
    await state.clear()
    await callback.answer()


@router.callback_query(
    F.data == "activate_user", flags={"allow_anonymous": True}
)
async def activate_user(
    callback: CallbackQuery, user: User, repository: UserRepository
):
    if user.is_active:
        await callback.message.answer(
            "Ваш аккаунт активен, дополнительных действий не требуется. "
            "Вы можете продложить работу с ботом в главном меню.",
            reply_markup=switch_to_main,
        )
        return

    elif not user.is_anonymous and not user.is_active:
        activated = repository.update_user(user.id, is_active=True)

        if activated:
            await callback.message.answer(
                "Ваш аккаунт снова активен.\n"
                "Вы можете продложить работу с ботом в главном меню.",
                reply_markup=switch_to_main,
            )

        else:
            await callback.message.answer(
                "Что-то пошло не так при активации Вашего аккаунта.\n"
                "Обратитесь в поддержку."
            )
    else:
        await callback.message.answer(
            "Ваш акканут отсутствует в системе. Зарегистритруйтесь, "
            "нажав кнопку ниже.",
            reply_markup=user_signup_menu,
        )
        return

    await callback.answer()


@router.callback_query(
    F.data == "delete_user", flags={"allow_anonymous": True}
)
async def delete_user(
    callback: CallbackQuery, user: User, repository: UserRepository
):
    if user.is_active:
        deactivated = repository.update_user(user.id, is_active=False)
        if deactivated:
            await callback.message.answer(
                "Ваш аккаунт успешно удален. Ваши данные будут доступны "
                "следующие 10 дней. Если вы измените свое решение, то "
                "сможете восстановить свой аккаунт в течение этого времени,"
                " воспользовавшись копкой ниже. Да прибудет с Вами сила.",
                reply_markup=user_activation_menu,
            )
        else:
            await callback.message.answer(
                "Что-то пошло не так при удалении Вашего аккаунта."
                "Обратитесь в поддержку."
            )
    elif not user.is_anonymous and not user.is_active:
        await callback.message.answer(
            "Ваш акканут запланирован к удалению."
            "Вы можете остановить процедуру удаления, нажав кнопку ниже.",
            reply_markup=user_activation_menu,
        )
    else:
        await callback.message.answer(
            "Вы пытаетесь удалить несуществующий аккаунт. Если вы когда-то "
            "пользовались ботом и желаете удалить ваши данные, то эти данные "
            "уже были удалены, дополнительных действий не требуется."
            "Вы можете зарегистрировать новый аккаунт, нажав на кнопку ниже.",
            reply_markup=user_signup_menu,
        )

    await callback.answer()


@router.callback_query(F.data == "show_user_profile")
async def show_user_profile(callback: CallbackQuery):
    await callback.message.answer(
        "Меню управления профилем. "
        "Со временем здесь могут появиться новые функции",
        reply_markup=user_profile_menu,
    )

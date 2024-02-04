from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.replies import keyboards, buttons, prompts
from app.bot.filters import BudgetCurrencyFilter
from app.bot.middlewares import UserRepositoryMiddleWare
from app.bot.states import UserCreateState
from app.db.models import User
from app.db.repository import UserRepository
from . import shared

router = Router()
router.callback_query.middleware(UserRepositoryMiddleWare())


@router.callback_query(
    F.data == shared.signup_user, flags={"allow_anonymous": True}
)
async def signup_user(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
):
    if user.is_active:
        await callback.message.answer(
            "Вы уже зарегистрированы в системе. "
            "Вы можете продложить работу с ботом в главном меню.",
            reply_markup=keyboards.button_menu(buttons.main_menu),
        )
        return

    elif user.is_anonymous:
        await state.update_data(tg_id=callback.from_user.id)
        await callback.message.answer(
            prompts.choose_budget_currency,
            reply_markup=keyboards.create_callback_buttons(
                button_names={
                    "изменить": "set_currency",
                    "принять": "finish",
                },
                callback_prefix="create_user",
            ),
        )

    else:
        await callback.message.answer(
            "Ранее Вы уже пользовались Бюджетным ботом, "
            "но решили перестать им пользоваться."
            "Вы можете продолжить работу со своими бюджетами, "
            "нажав кнопку активации ниже.",
            reply_markup=keyboards.button_menu(
                buttons.activate_user,
                buttons.cancel_operation,
            ),
        )
        return

    await state.set_state(UserCreateState.wait_for_action)
    await callback.answer()


@router.callback_query(
    UserCreateState.wait_for_action,
    F.data == "create_user_set_currency",
    flags={"allow_anonymous": True},
)
async def signup_user_request_currency(
    callback: CallbackQuery, state: FSMContext
):
    await callback.message.answer(prompts.budget_currency_description)
    await state.set_state(UserCreateState.set_budget_currency)
    await callback.answer()


@router.message(
    UserCreateState.set_budget_currency,
    BudgetCurrencyFilter(),
    flags={"allow_anonymous": True},
)
async def signup_user_set_currency(
    message: Message, state: FSMContext, filtered_budget_currency: str | None
):
    if filtered_budget_currency is None:
        await message.answer(
            prompts.invalid_budget_currency_description,
            reply_markup=keyboards.button_menu(buttons.cancel_operation),
        )
        return

    await state.update_data(budget_currency=filtered_budget_currency)
    await message.answer(
        f"Валюта Вашего бюджета - `{filtered_budget_currency}`."
        "Завершите регистрацию, нажав на кнопку Завершить.",
        reply_markup=keyboards.create_callback_buttons(
            button_names={
                "Завершить": "finish",
            },
            callback_prefix="create_user",
        ),
    )
    await state.set_state(UserCreateState.wait_for_action)


@router.callback_query(
    UserCreateState.wait_for_action,
    F.data == "create_user_finish",
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
            reply_markup=keyboards.button_menu(buttons.main_menu),
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
            reply_markup=keyboards.button_menu(buttons.main_menu),
        )
        return

    elif not user.is_anonymous and not user.is_active:
        activated = repository.update_user(user.id, is_active=True)

        if activated:
            await callback.message.answer(
                "Ваш аккаунт снова активен.\n"
                "Вы можете продложить работу с ботом в главном меню.",
                reply_markup=keyboards.button_menu(buttons.main_menu),
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
            reply_markup=keyboards.button_menu(buttons.signup_user),
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
                reply_markup=keyboards.button_menu(
                    buttons.activate_user,
                    buttons.main_menu,
                ),
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
            reply_markup=keyboards.button_menu(buttons.activate_user),
        )
    else:
        await callback.message.answer(
            "Вы пытаетесь удалить несуществующий аккаунт. Если вы когда-то "
            "пользовались ботом и желаете удалить ваши данные, то эти данные "
            "уже были удалены, дополнительных действий не требуется."
            "Вы можете зарегистрировать новый аккаунт, нажав на кнопку ниже.",
            reply_markup=keyboards.button_menu(buttons.signup_user),
        )

    await callback.answer()


@router.callback_query(F.data == "show_user_profile")
async def show_user_profile(callback: CallbackQuery):
    await callback.message.answer(
        "Меню управления профилем. "
        "Со временем здесь могут появиться новые функции",
        reply_markup=keyboards.button_menu(
            buttons.delete_user,
            buttons.main_menu,
        ),
    )

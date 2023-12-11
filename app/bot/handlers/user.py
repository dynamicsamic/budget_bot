from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot import keyboards
from app.bot.middlewares import AddUserControllerMiddleWare
from app.db.models import User
from app.db.queries.core import user_controller

router = Router()
router.callback_query.middleware(AddUserControllerMiddleWare())


@router.callback_query(
    F.data == "signup_user", flags={"allow_anonymous": True}
)
async def signup_user(
    callback: CallbackQuery, user: User, user_controller: user_controller
):
    if user.is_active:
        await callback.message.answer(
            "Вы уже зарегистрированы в системе. "
            "Вы можете продложить работу с ботом в главном меню.",
            reply_markup=keyboards.button_menu(keyboards.buttons.main_menu),
        )
        return

    elif user.is_anonymous:
        created = user_controller.create_user(tg_id=callback.from_user.id)
        if created is not None:
            await callback.message.answer(
                "Поздравляем! Вы успешно зарегистрированы в системе.\n"
                "Вы можете продложить работу с ботом в главном меню.",
                reply_markup=keyboards.button_menu(
                    keyboards.buttons.main_menu
                ),
            )

        else:
            await callback.message.answer(
                "Что-то пошло не так при регистрации.\nОбратитесь в поддержку."
            )
    else:
        await callback.message.answer(
            "Ранее Вы уже пользовались Бюджетным ботом, "
            "но решили перестать им пользоваться."
            "Вы можете продолжить работу со своими бюджетами, "
            "нажав кнопку активации ниже.",
            reply_markup=keyboards.button_menu(
                keyboards.buttons.activate_user,
                keyboards.buttons.cancel_operation,
            ),
        )
        return

    await callback.answer()


@router.callback_query(
    F.data == "activate_user", flags={"allow_anonymous": True}
)
async def activate_user(
    callback: CallbackQuery, user: User, user_controller: user_controller
):
    if user.is_active:
        await callback.message.answer(
            "Ваш аккаунт активен, дополнительных действий не требуется. "
            "Вы можете продложить работу с ботом в главном меню.",
            reply_markup=keyboards.button_menu(keyboards.buttons.main_menu),
        )
        return

    elif not user.is_anonymous and not user.is_active:
        activated = user_controller.update_user(user.id, is_active=True)

        if activated:
            await callback.message.answer(
                "Ваш аккаунт снова активен.\n"
                "Вы можете продложить работу с ботом в главном меню.",
                reply_markup=keyboards.button_menu(
                    keyboards.buttons.main_menu
                ),
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
            reply_markup=keyboards.button_menu(keyboards.buttons.signup_user),
        )
        return

    await callback.answer()


@router.callback_query(
    F.data == "delete_user", flags={"allow_anonymous": True}
)
async def delete_user(
    callback: CallbackQuery, user: User, user_controller: user_controller
):
    if user.is_active:
        deactivated = user_controller.update_user(user.id, is_active=False)
        if deactivated:
            await callback.message.answer(
                "Ваш аккаунт успешно удален. Ваши данные будут доступны "
                "следующие 10 дней. Если вы измените свое решение, то "
                "сможете восстановить свой аккаунт в течение этого времени,"
                " воспользовавшись копкой ниже. Да прибудет с Вами сила.",
                reply_markup=keyboards.button_menu(
                    keyboards.buttons.activate_user,
                    keyboards.buttons.main_menu,
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
            reply_markup=keyboards.button_menu(
                keyboards.buttons.activate_user
            ),
        )
    else:
        await callback.message.answer(
            "Вы пытаетесь удалить несуществующий аккаунт. Если вы когда-то "
            "пользовались ботом и желаете удалить ваши данные, то эти данные "
            "уже были удалены, дополнительных действий не требуется."
            "Вы можете зарегистрировать новый аккаунт, нажав на кнопку ниже.",
            reply_markup=keyboards.button_menu(keyboards.buttons.signup_user),
        )

    await callback.answer()


@router.callback_query(F.data == "show_user_profile")
async def show_user_profile(callback: CallbackQuery):
    await callback.message.answer(
        "Меню управления профилем. "
        "Со временем здесь могут появиться новые функции",
        reply_markup=keyboards.button_menu(
            keyboards.buttons.delete_user,
            keyboards.buttons.main_menu,
        ),
    )

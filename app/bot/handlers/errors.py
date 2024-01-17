import logging

from aiogram import Bot, Router, types
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.exc import SQLAlchemyError

from app.bot import keyboards, prompts
from app.exceptions import (
    EmptyModelKwargs,
    InvalidCallbackData,
    InvalidCategoryName,
    InvalidModelArgType,
    InvalidModelAttribute,
    ModelInstanceDuplicateAttempt,
    ModelInstanceNotFound,
    RepositoryValidationError,
    UnknownDataBaseException,
)
from app.utils import aiogram_log_handler
from config import config

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)

router = Router(name=__name__)
serverside_errors = (
    RepositoryValidationError,
    InvalidCallbackData,
    UnknownDataBaseException,
    EmptyModelKwargs,
    InvalidModelArgType,
    InvalidModelAttribute,
    SQLAlchemyError,
    ModelInstanceNotFound,
)


@router.errors(ExceptionTypeFilter(*serverside_errors))
async def serverside_error_handler(
    error_event: types.ErrorEvent, bot: Bot, state: FSMContext
):
    error_message = (
        f"Error caught: {repr(error_event.exception)} "
        f"while processing {error_event.update}"
    )
    logger.error(error_message)

    support_id = int(config.support_manager_id.get_secret_value())
    await bot.send_message(support_id, text=error_message)

    update = error_event.update

    if update.message is not None:
        message = update.message
    elif update.callback_query is not None:
        message = update.callback_query.message

    await message.answer(prompts.serverside_error_response)
    await state.clear()


@router.errors(ExceptionTypeFilter(InvalidCategoryName))
async def invalid_category_name_handler(error_event: types.ErrorEvent):
    logger.info(f"Invalid user input triggered {error_event.exception}")
    await error_event.update.message.answer(
        "Недопустимое название категории."
        f"{prompts.category_name_description}"
    )


@router.errors(ExceptionTypeFilter(ModelInstanceDuplicateAttempt))
async def instance_duplicate_attempt_handler(error_event: types.ErrorEvent):
    exception: ModelInstanceDuplicateAttempt = error_event.exception
    await error_event.update.message.answer(
        f"{exception}. Придумайте новое значение и повторите попытку "
        "или прервите процедуру, нажав на кнопку отмены.",
        reply_markup=keyboards.button_menu(keyboards.buttons.cancel_operation),
    )
    logger.info(
        f"User {exception.user_tg_id} triggered exception: {repr(exception)}"
    )

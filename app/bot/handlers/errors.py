import logging

from aiogram import Bot, Router, types
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.context import FSMContext

from app.bot.prompts import callback_error_response
from app.exceptions import InvalidCallbackData
from app.utils import aiogram_log_handler
from config import config

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)

router = Router(name=__name__)


@router.errors(ExceptionTypeFilter(InvalidCallbackData))
async def invalid_callback_data_handler(
    error_event: types.ErrorEvent, bot: Bot, state: FSMContext
):
    error_message = (
        f"Error caught: {repr(error_event.exception)} "
        f"while processing {error_event.update}"
    )
    logger.error(error_message)
    support_id = int(config.support_manager_id.get_secret_value())
    await bot.send_message(support_id, text=error_message)
    await error_event.update.callback_query.message.answer(
        callback_error_response
    )
    await state.clear()

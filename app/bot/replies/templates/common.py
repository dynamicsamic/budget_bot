from aiogram.types import ReplyKeyboardRemove

from app.bot.replies import prompts
from app.bot.replies.keyboards import common, user

from . import Template

start_message_anonymous = Template(
    prompts.start_message_anonymous, user.signup_menu
)
start_message_inactive = Template(
    prompts.start_message_inactive, user.activation_menu
)
start_message_active = Template(
    prompts.start_message_active, common.switch_to_main_or_cancel
)
cancel_operation = Template(
    prompts.cancel_operation_note, ReplyKeyboardRemove()
)
main_menu = Template(prompts.main_menu_note, common.show_main_menu)
redirect_anonymous = Template(prompts.signup_to_proceed, user.signup_menu)
redirect_inactive = Template(prompts.activate_to_proceed, user.activation_menu)
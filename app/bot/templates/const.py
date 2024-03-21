from aiogram.types import ReplyKeyboardRemove

from app.bot.templates import texts

from . import keyboards as kbd
from .base import Template

##########
# Common #
##########
start_message_anonymous = Template(
    texts.start_message_anonymous, kbd.signup_menu
)
start_message_inactive = Template(
    texts.start_message_inactive, kbd.activation_menu
)
start_message_active = Template(
    texts.start_message_active, kbd.switch_to_main_or_cancel
)
cancel_operation = Template(texts.cancel_operation_note, ReplyKeyboardRemove())
main_menu = Template(texts.main_menu_note, kbd.show_main_menu)
redirect_anonymous = Template(texts.signup_to_proceed, kbd.signup_menu)
redirect_inactive = Template(texts.activate_to_proceed, kbd.activation_menu)


###########
#  Error  #
###########
invalid_budget_currency = Template(
    texts.invalid_budget_currency,
    kbd.switch_to_main_or_cancel,
)
invalid_category_name = Template(
    texts.invalid_category_name,
    kbd.switch_to_main_or_cancel,
)
serverside_error = Template(
    texts.serverside_error_response, kbd.switch_to_main
)

##########
#  User  #
##########
choose_signup_type = Template(texts.choose_signup_type, kbd.choose_signup_type)
advanced_signup_menu = Template(
    texts.advanced_signup_description, kbd.get_budget_currency_menu
)
budget_currency_description = Template(texts.budget_currency_description)
user_activation_summary = Template(
    texts.user_activation_summary, kbd.switch_to_main
)
user_profile = Template(texts.user_profile_description, kbd.user_profile_menu)
user_delete_summary = Template(texts.user_delete_summary, kbd.activation_menu)


############
# Category #
############
category_name_description = Template(
    texts.category_name_description, kbd.switch_to_main_or_cancel
)
category_type_selection = Template(
    texts.choose_category_type, kbd.category_type_menu
)
zero_category = Template(texts.zero_category_note, kbd.create_category_menu)
category_delete_summary = Template(
    texts.category_delete_summary, kbd.show_categories_menu
)
category_update_start = Template(
    texts.update_category_invite_user, kbd.category_update_options
)
category_empty_update = Template(
    texts.update_without_changes, kbd.show_categories_menu
)
###########
#  Entry  #
###########
entry_sum_description = Template(
    texts.entry_sum_description, kbd.switch_to_main_or_cancel
)

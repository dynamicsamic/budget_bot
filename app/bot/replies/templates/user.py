from app.bot.replies import prompts
from app.bot.replies.keyboards import common as comkbd
from app.bot.replies.keyboards import user as uskbd
from app.db.models import User

from . import Template

choose_signup_type = Template(
    prompts.choose_signup_type, uskbd.choose_signup_type
)

advanced_signup_menu = Template(
    prompts.advanced_signup_description, uskbd.set_budget_currency_menu
)

budget_currency_description = Template(prompts.budget_currency_description)

show_activation_summary = Template(
    prompts.user_activation_success, comkbd.switch_to_main
)

show_profile = Template(
    prompts.user_profile_description, uskbd.user_profile_menu
)

show_delete_summary = Template(
    prompts.user_delete_success, uskbd.user_activation_menu
)


def show_signup_summary(user: User) -> Template:
    return Template(
        prompts.user_signup_success(user), uskbd.switch_to_user_profile
    )


def show_currency(budget_currency: str) -> Template:
    return Template(
        prompts.signup_user_show_currency_and_finish(budget_currency),
        uskbd.finish_advanced_signup,
    )

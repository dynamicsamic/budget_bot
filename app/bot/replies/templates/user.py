from app.bot.replies import prompts
from app.bot.replies.keyboards import user

from . import Template

choose_signup_type = Template(
    prompts.choose_signup_type, user.choose_signup_type
)
advanced_signup_menu = Template(
    prompts.advanced_signup_description, user.set_budget_currency_menu
)
budget_currency_description = Template(prompts.budget_currency_description)

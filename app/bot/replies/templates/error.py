from app.bot.replies import prompts
from app.bot.replies.keyboards import common as comkbd
from app.exceptions import ModelInstanceDuplicateAttempt

from . import Template

invalid_budget_currency = Template(
    prompts.invalid_budget_currency,
    comkbd.switch_to_main_or_cancel,
)

invalid_category_name = Template(
    prompts.invalid_category_name,
    comkbd.switch_to_main_or_cancel,
)

serverside_error = Template(
    prompts.serverside_error_response, comkbd.switch_to_main
)


def instance_duplicate_attempt(
    exception: ModelInstanceDuplicateAttempt,
) -> Template:
    return Template(
        prompts.show_instance_duplicate_attempt_prompt(exception),
        comkbd.switch_to_main_or_cancel,
    )

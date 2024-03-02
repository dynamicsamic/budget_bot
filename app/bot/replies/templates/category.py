from app.bot.replies import prompts
from app.bot.replies.keyboards import category as catkbd
from app.bot.replies.keyboards import common as comkbd

from . import Template

name_description = Template(
    prompts.category_name_description, comkbd.switch_to_main_or_cancel
)
type_selection = Template(
    prompts.choose_category_type, catkbd.category_type_menu
)

zero_category = Template(
    prompts.zero_category_note, catkbd.create_category_menu
)


def create_summary(category) -> Template:
    return Template(
        prompts.show_new_category_summary(category),
        catkbd.show_categories_menu,
    )

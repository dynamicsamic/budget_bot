from typing import Iterable

from app.bot.replies import prompts
from app.bot.replies.keyboards import category as catkbd
from app.bot.replies.keyboards import common as comkbd
from app.db.models import Category
from app.utils import OffsetPaginator

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


def show_paginated_categories(
    categories: Iterable[Category], paginator: OffsetPaginator
) -> Template:
    return Template(
        prompts.category_choose_action,
        catkbd.categories_paginated_list(categories, paginator),
    )

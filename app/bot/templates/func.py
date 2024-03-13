from typing import Iterable

from app.bot.templates import texts
from app.db.models import Category, CategoryType, User
from app.exceptions import ModelInstanceDuplicateAttempt
from app.utils import OffsetPaginator

from . import keyboards as kbd
from .base import Template


###########
#  Error  #
###########
def instance_duplicate_attempt(
    exception: ModelInstanceDuplicateAttempt,
) -> Template:
    return Template(
        texts.show_instance_duplicate_attempt_prompt(exception),
        kbd.switch_to_main_or_cancel,
    )


##########
#  User  #
##########
def show_signup_summary(user: User) -> Template:
    return Template(
        texts.user_signup_summary.format(user_data=user.render()),
        kbd.switch_to_user_profile,
    )


def confirm_updated_currency(budget_currency: str) -> Template:
    return Template(
        texts.budget_currency_update_warning.format(
            budget_currency=budget_currency
        ),
        kbd.confirm_updated_currency_menu,
    )


def show_signup_currency(budget_currency: str) -> Template:
    return Template(
        texts.user_signup_currency_note.format(
            budget_currency=budget_currency
        ),
        kbd.finish_advanced_signup,
    )


def show_currency_update_summary(budget_currency: str) -> Template:
    return Template(
        texts.show_lite_update_summary(name="Валюта", value=budget_currency),
        kbd.switch_to_user_profile,
    )


############
# Category #
############
def show_category_create_summary(category: Category) -> Template:
    return Template(
        texts.show_new_category_summary(category),
        kbd.show_categories_menu,
    )


def show_paginated_categories(
    categories: Iterable[Category], paginator: OffsetPaginator
) -> Template:
    return Template(
        texts.category_choose_action,
        kbd.categories_paginated_list(categories, paginator),
    )


def show_category_control_options(category_id: int) -> Template:
    return Template(
        texts.choose_action, kbd.category_choose_update_delete(category_id)
    )


def show_delete_category_warning(category: Category) -> Template:
    return Template(
        texts.delete_category_warning.format(
            category_name=category.name, num_entries=category.num_entries
        ),
        kbd.delete_category_warning(category.id),
    )


def show_updated_category_name(category_name: str) -> Template:
    text = texts.category_update_name_summary.format(
        category_name=category_name
    )
    return Template(
        f"{text}{texts.category_update_note}", kbd.category_update_options
    )


def show_updated_category_type(category_type: CategoryType) -> Template:
    text = texts.category_update_type_summary.format(
        category_type=category_type
    )
    return Template(
        f"{text}{texts.category_update_note}", kbd.category_update_options
    )


def show_category_update_summary(category: Category) -> Template:
    text = texts.update_summary.format(
        obj_name=category._public_name, obj_data=category.render()
    )
    return Template(text, kbd.show_categories_menu)


###########
#  Entry  #
###########

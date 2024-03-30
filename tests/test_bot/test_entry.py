import pytest
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import Update

from app.bot import string_constants as sc
from app.bot.states import CreateEntry
from app.bot.templates import func
from app.db.models import CategoryType
from app.db.repository import CategoryRepository
from app.utils import OffsetPaginator

from ..test_utils import (
    EXPENSES_SAMPLE,
    INCOME_SAMPLE,
    TARGET_USER_ID,
    assert_uses_template,
)
from .conftest import generic_callback_query as callback
from .conftest import generic_message as msg


@pytest.fixture
def category_repo(persistent_db_session):
    return CategoryRepository(persistent_db_session)


@pytest.mark.asyncio
async def test_create_income(create_test_data, category_repo, requester):
    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=msg(text=f"/{sc.CREATE_INCOME_COMMAND}"),
        ),
    )

    page_limit = 5
    paginator = OffsetPaginator(
        sc.ENTRY_CATEGORY_PAGE, INCOME_SAMPLE, page_limit
    )
    categories = category_repo.get_user_categories(
        TARGET_USER_ID, category_type=CategoryType.INCOME
    )

    answer = requester.read_last_sent_message()
    assert_uses_template(
        answer,
        func.show_paginated_income,
        categories=categories.result,
        paginator=paginator,
    )

    state = await requester.get_fsm_state()
    assert state == CreateEntry.choose_category

    state_data = await requester.get_fsm_state_data()
    assert state_data == {
        "user_id": TARGET_USER_ID,
        "category_type": CategoryType.INCOME,
        "paginator": paginator,
    }


@pytest.mark.asyncio
async def test_create_expense(create_test_data, category_repo, requester):
    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=msg(text=f"/{sc.CREATE_EXPENSE_COMMAND}"),
        ),
    )

    page_limit = 5
    paginator = OffsetPaginator(
        sc.ENTRY_CATEGORY_PAGE, EXPENSES_SAMPLE, page_limit
    )
    categories = category_repo.get_user_categories(
        TARGET_USER_ID, category_type=CategoryType.EXPENSES
    )

    answer = requester.read_last_sent_message()
    assert_uses_template(
        answer,
        func.show_paginated_expenses,
        categories=categories.result,
        paginator=paginator,
    )

    state = await requester.get_fsm_state()
    assert state == CreateEntry.choose_category

    state_data = await requester.get_fsm_state_data()
    assert state_data == {
        "user_id": TARGET_USER_ID,
        "category_type": CategoryType.EXPENSES,
        "paginator": paginator,
    }


@pytest.mark.asyncio
async def test_create_entry_show_next_paginated_income(
    create_test_data, category_repo, requester
):
    page_limit = 5
    paginator = OffsetPaginator(
        sc.ENTRY_CATEGORY_PAGE, INCOME_SAMPLE, page_limit
    )
    await requester.set_fsm_state(CreateEntry.choose_category)
    await requester.update_fsm_state_data(
        user_id=TARGET_USER_ID,
        category_type=CategoryType.INCOME,
        paginator=paginator,
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(
            update_id=1,
            callback_query=callback(data=f"{sc.ENTRY_CATEGORY_PAGE}:next"),
        ),
    )

    paginator.switch_next()
    categories = category_repo.get_user_categories(
        TARGET_USER_ID,
        offset=paginator.current_offset,
        category_type=CategoryType.INCOME,
    )
    answer = requester.read_last_sent_message()
    assert_uses_template(
        answer,
        func.show_paginated_categories,
        categories=categories.result,
        paginator=paginator,
    )

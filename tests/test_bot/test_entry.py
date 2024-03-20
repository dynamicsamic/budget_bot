from datetime import datetime

import pytest
from aiogram.methods import SendMessage
from aiogram.types import Message, Update

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
from .conftest import chat, user


@pytest.fixture
def category_repo(persistent_db_session):
    return CategoryRepository(persistent_db_session)


@pytest.mark.asyncio
async def test_create_income(create_test_data, category_repo, requester):
    msg = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=f"/{sc.CREATE_INCOME_COMMAND}",
    )

    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=msg,
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
    assert state == CreateEntry.category


@pytest.mark.asyncio
async def test_create_expense(create_test_data, category_repo, requester):
    msg = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=f"/{sc.CREATE_EXPENSE_COMMAND}",
    )

    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=msg,
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
    assert state == CreateEntry.category

from datetime import datetime

import pytest
from aiogram.enums import ChatType
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User

from app.bot.states import CreateCategory

from ..test_utils import clear_dispatcher_state, get_dispatcher_state

user = User(id=101, is_bot=False, first_name="User", username="username")
chat = Chat(id=1, type=ChatType.PRIVATE)
create_category_command = Message(
    message_id=1,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text="/create_category",
)


@pytest.mark.asyncio
async def test_cmd_create_category(create_test_data, mocked_bot, dispatcher):
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=create_category_command, update_id=1),
    )

    state = await get_dispatcher_state(dispatcher, mocked_bot, chat, user)

    assert state == CreateCategory.set_name
    await clear_dispatcher_state(dispatcher, mocked_bot, chat, user)

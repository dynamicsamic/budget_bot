from datetime import datetime

import pytest
from aiogram.enums import ChatType
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User

from app.bot.states import CreateCategory

user = User(id=101, is_bot=False, first_name="User", username="username")
chat = Chat(id=1, type=ChatType.PRIVATE)


@pytest.mark.asyncio
async def test_cmd_show_categories(create_test_data, mocked_bot, dispatcher):
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    msg = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="/show_categories",
    )
    print(dir(dispatcher))
    print(mocked_bot.session.responses)
    print(mocked_bot.session.requests)
    print(dispatcher.observers["message"].handlers)
    # result = await dispatcher._listen_update(Update(message=msg, update_id=1))
    # result = await dispatcher._process_update(bot, Update(message=msg, update_id=1))
    # result = await dispatcher._process_update(
    #     bot, Update(message=msg, update_id=1)
    # )
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=msg, update_id=1),
    )
    print(mocked_bot.session.requests)
    print(await dispatcher.fsm.get_context(mocked_bot, 1, 101).get_state())

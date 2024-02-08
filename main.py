import asyncio
import logging

from app.bot import bot, dp
from app.bot.handlers import router
from app.db import test_engine
from app.db.models import Base

logging.basicConfig(level=logging.INFO)


async def main():
    Base.metadata.create_all(test_engine)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

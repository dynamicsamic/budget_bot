import asyncio
import logging

from app.bot import bot, dp
from app.bot.handlers import callbacks, commands

logging.basicConfig(level=logging.INFO)


async def main():
    dp.include_routers(commands.router, callbacks.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

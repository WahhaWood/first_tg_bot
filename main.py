import asyncio
from bot import dp, bot
from handlers import client, admin


client.register_handler_client()
admin.register_handler_admin()

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
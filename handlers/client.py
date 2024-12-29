from bot import dp, bot
from pymongo import MongoClient
import config as con
from aiogram import types
from utils.func import add_active_chat, remove_active_chat, get_admin_ids, send_message_admins, check_admin, check_order
from utils.keyboard import main_keyboard
from aiogram.filters import Command
from handlers.admin import admin_start


client = MongoClient(con.MONGODB_URL)
db = client['telegram_bot']
config_collection = db['config']


async def start_message(message: types.Message):
    if check_admin(message.from_user.id):
        await admin_start(message)
    else:
        await client_start(message)

async def client_start(message: types.Message):
    await message.answer("Вітаємо! Ласкаво просимо до нашого магазину!🌟", reply_markup=main_keyboard)

async def order(message: types.Message):
    user_id = message.from_user
    result = check_order(user_id.id)
    if result:
        await message.answer("Ви вже зробили замовлення. Очікуйте на відповідь від нашого менеджера😊")
    else:
        await message.answer("Ваш запит прийнято! Очікуйте відповіді від нашого менеджера😊")
        add_active_chat(user_id.id, user_id.username)
        await send_message_admins(user_id)

async def catalog(message: types.Message):
    catalog_url = config_collection.find_one({"parameter": "channel_url"})["channel_url"]
    await message.answer(
        "Перейдіть до каналу нашого магазину, щоб побачити повний каталог товарів: \n"f"{catalog_url} 📚")

def register_handler_client():
    dp.message.register(start_message, Command('start'))
    dp.message.register(order, lambda message: message.text == "Зробити замовлення🛒")
    dp.message.register(catalog, lambda message: message.text == "Переглянути каталог🛍️")
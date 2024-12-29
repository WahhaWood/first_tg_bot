from bot import dp, bot
from aiogram import types
from utils.func import add_admin, get_orders, get_admin_ids, is_active_chat, add_active_chat, remove_active_chat, check_admin, get_active_dialogs
from utils.keyboard import main_admin_keyboard, admin_keyboard, main_keyboard
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, StateFilter
from time import sleep
from pymongo import MongoClient
from aiogram.fsm.storage.base import StorageKey
import config as con


client = MongoClient(con.MONGODB_URL)
db = client['telegram_bot']
admin_collection = db['admins']
active_chats_collection = db['active_chats']
config_collection = db['config']


class DialogStates(StatesGroup):
    active_dialog = State()

class AdminStates(StatesGroup):
    waiting_for_channel_url = State()
    waiting_for_admin_id = State()

async def admin_start(message: types.Message):
    if check_admin(message.from_user.id):
        await message.answer(f'Вітаємо! Ласкаво просимо до нашого магазину!🌟')
        await message.answer(f'Ви авторизувалися як адміністратор!🛠️', reply_markup=main_admin_keyboard)

async def admins_panel(message: types.Message):
    if check_admin(message.from_user.id):
        await message.answer(f"Ви відкрили адмін-панель🔧", reply_markup=admin_keyboard)

async def id_user(message: types.Message):
    if check_admin(message.from_user.id):
        await message.answer(f"Ось ваш ID: {message.from_user.id}")

async def show_orders(message: types.Message):
    if check_admin(message.from_user.id):
        if active_chats_collection.count_documents({}) > 0:
            active_chats = list(active_chats_collection.find())
            
            builder = InlineKeyboardBuilder()

            for chat in active_chats:
                user_id = chat['user_id']
                username = chat['username']
                button_text = f"{username} (ID: {user_id})"
                builder.add(types.InlineKeyboardButton(text=button_text, callback_data=f'order_{user_id}'))

            builder.adjust(1)
            await message.reply("Оберіть замовлення:", reply_markup=builder.as_markup())
        else:
            await message.reply("Наразі у вас немає замовлень.")

async def end_dialog_callback(user_id, state: FSMContext):
    await state.clear()
    if active_chats_collection.find_one({'admin_id': user_id}):
        user_id_ = active_chats_collection.find_one({'admin_id': user_id})['user_id']
        await bot.send_message(user_id, "Діалог з користувачем завершено❌", reply_markup=main_admin_keyboard)
        await bot.send_message(user_id_, "Діалог з менеджером завершено❌", reply_markup=main_keyboard)
        active_chats_collection.update_one(
            {'admin_id': user_id},
            {'$set': {'active-status': False}, '$unset': {'admin_id': ""}}
        )
    if active_chats_collection.find_one({'user_id': user_id}):
        user_id_ = active_chats_collection.find_one({'user_id': user_id})['admin_id']
        await bot.send_message(user_id, "Діалог з менеджером завершено❌", reply_markup=main_keyboard)
        await bot.send_message(user_id_, "Діалог з користувачем завершено❌", reply_markup=main_admin_keyboard)
        active_chats_collection.update_one(
            {'user_id': user_id},
            {'$set': {'active-status': False}, '$unset': {'admin_id': ""}}
        )

    state_with: FSMContext = FSMContext(
        storage=dp.storage,
        key=StorageKey(
            chat_id=user_id_,
            user_id=user_id_,
            bot_id=bot.id
        )
    )
    await state_with.update_data()
    await state_with.clear()

async def handle_dialog_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text == "Завершити діалог❌":
        await end_dialog_callback(user_id, state)
        return

    if message.sticker:
        sticker_id = message.sticker.file_id
        if active_chats_collection.find_one({'admin_id': user_id}):
            await bot.send_sticker(active_chats_collection.find_one({'admin_id': user_id})['user_id'], sticker_id)
        if active_chats_collection.find_one({'user_id': user_id}):
            await bot.send_sticker(active_chats_collection.find_one({'user_id': user_id})['admin_id'], sticker_id)
        return

    if active_chats_collection.find_one({'admin_id': user_id}):
        await bot.send_message(active_chats_collection.find_one({'admin_id': user_id})['user_id'], f"{message.text}")
    if active_chats_collection.find_one({'user_id': user_id}):
        await bot.send_message(active_chats_collection.find_one({'user_id': user_id})['admin_id'], f"{message.text}")

async def close_order(callback_query: types.CallbackQuery):
    if check_admin(callback_query.from_user.id):
        user_id = int(callback_query.data.split('_')[2])
        admin_id = callback_query.from_user.id
        
        result = active_chats_collection.delete_one({'user_id': user_id})
        
        if result.deleted_count > 0:
            await bot.send_message(admin_id, f"Замовлення користувача з ID {user_id} успішно закрито✅", reply_markup=main_admin_keyboard)
            
            try:
                await bot.send_message(user_id, "Ваше замовлення було закрито адміністратором✅", reply_markup=main_keyboard)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        else:
            await callback_query.answer("Помилка: Замовлення не знайдено.")
    

async def process_order(callback_query: types.CallbackQuery):
    if check_admin(callback_query.from_user.id):
        user_id = int(callback_query.data.split('_')[1])
        chat = active_chats_collection.find_one({'user_id': user_id})
        builder = InlineKeyboardBuilder()

        if chat:
            builder.add(
                types.InlineKeyboardButton(text="Розпочати діалог💬", callback_data=f'start_dialog_{user_id}'),
                types.InlineKeyboardButton(text="Закрити замовлення❌", callback_data=f'close_order_{user_id}')
            )
            username = chat['username']
            active_status = "Активен" if chat.get('active-status') else "Неактивен"
            
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(
                callback_query.from_user.id, 
                f"Информация о заказе:\nUsername: {username}\nUser ID: {user_id}\nСтатус: {active_status}",
                reply_markup=builder.as_markup()
            )
        else:
            await bot.answer_callback_query(callback_query.id, text="Замовлення не знайдено.")

async def new_admin(message: types.Message):
    if check_admin(message.from_user.id):
        try:
            id_new_admin = int(command.args)
            
            add_admin(id_new_admin)
            await message.answer(f"Успішно додано нового адміністратора з ID {id_new_admin}!")
        except ValueError:
            await message.answer("Будь ласка, вкажіть коректний ID.")
        except Exception as e:
            await message.answer(f"Сталася помилка: {e}")

async def exit_admin_panel(message: types.Message):
    if check_admin(message.from_user.id):
        await message.answer(f"Ви вийшли з адмін-панелі✅", reply_markup=main_admin_keyboard)

async def start_dialog(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[2])

    active_chats_collection.update_one(
        {'user_id': user_id}, 
        {'$set': {'active-status': True, 'admin_id': callback_query.from_user.id}},
        upsert=True
    )

    await state.set_state(DialogStates.active_dialog)
    
    state_with: FSMContext = FSMContext(
        storage=dp.storage,
        key=StorageKey(
            chat_id=user_id,
            user_id=user_id,
            bot_id=bot.id
        )
    )
    await state_with.update_data()
    await state_with.set_state(DialogStates.active_dialog)

    dialog_buttons = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Завершити діалог❌", callback_data=f"end_dialog_{user_id}", resize_keyboard=True)]])

    await bot.send_message(callback_query.from_user.id, "Діалог з користувачем розпочато.", reply_markup=dialog_buttons)
    await bot.send_message(user_id, "Діалог розпочато! Будь ласка, очікуйте повідомлень від менеджера.", reply_markup=dialog_buttons)

async def change_channel_url_button(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        await message.reply("Відправте нове посилання на канал:")
        await state.set_state(AdminStates.waiting_for_channel_url)

async def update_channel_url(message: types.Message, state: FSMContext):
    new_url = message.text

    result = config_collection.update_one(
        {"parameter": "channel_url"},
        {"$set": {"channel_url": new_url}},
        upsert=True
    )

    if result.modified_count > 0 or result.upserted_id:
        await message.reply("Посилання на канал успішно оновлено🔗")
    else:
        await message.reply("Сталася помилка під час оновлення посилання⚠️")
    
    await state.clear()

async def add_new_admin_button(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        await message.reply("Відправте ID нового адміністратора:")
        await state.set_state(AdminStates.waiting_for_admin_id)

async def add_new_admin(message: types.Message, state: FSMContext):
    try:
        new_admin_id = int(message.text)

        result = admin_collection.insert_one({'admin_id': new_admin_id})

        if result.inserted_id:
            await message.reply(f"Нового адміністратора з ID {new_admin_id} успішно додано✨")
        else:
            await message.reply("Адміністратор з таким ID вже існує⚠️")
        
    except ValueError:
        await message.reply("Будь ласка, введіть коректний числовий ID⚠️")
    
    await state.clear()

def register_handler_admin():
    dp.message.register(admins_panel, lambda message: message.text == "Адмін-панель🔧")
    dp.message.register(id_user, Command('id'))
    dp.message.register(show_orders, lambda message: message.text == "Переглянути замовлення📋")
    dp.message.register(exit_admin_panel, lambda message: message.text == "Вийти з адмін-панелі❌")
    dp.message.register(change_channel_url_button, lambda message: message.text == "Змінити посилання на канал🔗")
    dp.message.register(add_new_admin_button, lambda message: message.text == "Додати нового адміністратора✨")
    
    dp.callback_query.register(process_order, lambda callback_query: callback_query.data.startswith('order_'))
    dp.callback_query.register(start_dialog, lambda callback_query: callback_query.data.startswith('start_dialog_'))
    dp.callback_query.register(close_order, lambda callback_query: callback_query.data.startswith('close_order_'))

    dp.message.register(handle_dialog_message, DialogStates.active_dialog)
    dp.message.register(update_channel_url, AdminStates.waiting_for_channel_url)
    dp.message.register(add_new_admin, AdminStates.waiting_for_admin_id)
    

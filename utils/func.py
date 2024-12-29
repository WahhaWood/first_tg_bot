from pymongo import MongoClient
import config as con
from bot import dp, bot


client = MongoClient(con.MONGODB_URL)
db = client['telegram_bot']
admin_collection = db['admins']
active_chats_collection = db['active_chats']

def add_admin(admin_id):
    if not admin_collection.find_one({'admin_id': admin_id}):
        admin_collection.insert_one({'admin_id': admin_id})

def get_orders():
    return list(active_chats_collection.find())

def get_admin_ids():
    return [admin['admin_id'] for admin in admin_collection.find()]

def is_active_chat(user_id):
    return active_chats_collection.count_documents({'user_id': user_id}) > 0

def add_active_chat(user_id, username):
    if not is_active_chat(user_id):
        active_chats_collection.insert_one({'user_id': user_id, 'username': username, 'active-status': False})

def remove_active_chat(user_id):
    active_chats_collection.delete_one({'user_id': user_id})

def check_admin(user_id):
    return admin_collection.find_one({'admin_id': user_id})

def check_order(user_id):
    return active_chats_collection.find_one({'user_id': user_id})

async def send_message_admins(user_id):
    for admin_id in get_admin_ids():
        content = f"Пользователь <b>{user_id.username}</b> с ID <b>{user_id.id}</b> хочет сделать заказ."
        await bot.send_message(admin_id, content, parse_mode="HTML") 

def get_active_dialogs():
    return active_chats_collection.find({'active-status': True})
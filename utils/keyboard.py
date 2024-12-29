import aiogram
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot import dp, bot


main_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Зробити замовлення🛒"), KeyboardButton(text="Переглянути каталог🛍️")]],resize_keyboard=True)

main_admin_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Зробити замовлення🛒"), KeyboardButton(text="Переглянути каталог🛍️")],[KeyboardButton(text="Адмін-панель🔧")]],resize_keyboard=True)

admin_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Переглянути замовлення📋"), KeyboardButton(text="Додати нового адміністратора✨")], [KeyboardButton(text="Змінити посилання на канал🔗"), KeyboardButton(text="Вийти з адмін-панелі❌")]],resize_keyboard=True)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="💰 Конвертер"), KeyboardButton(text="⭐ Избранное")],
        [KeyboardButton(text="🔔 Уведомления"), KeyboardButton(text="🔄 Главный экран")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_converter_keyboard():
    
    buttons = [
        [KeyboardButton(text="↩️ На главный")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_favorites_keyboard():

    buttons = [
        [KeyboardButton(text="Изменить список"), KeyboardButton(text="↩️ На главный")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_edit_favorites_keyboard():

    buttons = [
        [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
        [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="↩️ На главный")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_notifications_keyboard():
    buttons = [
        [KeyboardButton(text="➕ Создать уведомление"), KeyboardButton(text="🗑️ Удалить уведомление")],
        [KeyboardButton(text="↩️ На главный")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

from keyboards import *
from database import *
from api import *

# Состояния для FSM
class ConverterStates(StatesGroup):
    waiting_for_currency1 = State()
    waiting_for_amount = State()
    waiting_for_currency2 = State()

class FavoriteStates(StatesGroup):
    waiting_for_edit_choice = State()
    waiting_for_fav_currency1 = State()
    waiting_for_fav_currency2 = State()

class NotificationStates(StatesGroup):
    waiting_for_asset = State()
    waiting_for_percent = State()
    waiting_for_delete_asset = State()

# Обработчики команд
async def cmd_start(message: types.Message):
    await register_user(message.from_user.id)
    await message.answer(
        "Добро пожаловать в конвертер валют!",
        reply_markup=get_main_keyboard()
    )

async def cmd_help(message: types.Message):
    help_text = """
*Помощь по использованию бота*

Этот бот поможет вам конвертировать криптовалюты, отслеживать избранные пары и получать уведомления об изменениях цен.

*Основные функции:*

💰 *Конвертер* - позволяет конвертировать одну валюту в другую.
   Как использовать:
   1. Нажмите кнопку "Конвертер"
   2. Введите исходную валюту (например: BTC)
   3. Введите количество
   4. Введите целевую валюту
   5. Получите результат

⭐ *Избранное* - показывает ваши любимые валютные пары.
   - Вы можете сохранить до 5 пар
   - Для изменения списка нажмите "Изменить список"
   - Выберите позицию (1-5) и введите две валюты

🔔 *Уведомления* - создавайте уведомления об изменениях цен.
   - Нажмите "Создать уведомление"
   - Введите актив (например: BTC)
   - Введите процент изменения
   - Бот будет уведомлять вас при изменении цены на указанный процент

🔄 *Главный экран* - возвращает в главное меню.

*Дополнительно:*
- Данные берутся с биржи Bybit в реальном времени
- Уведомления проверяются каждую минуту

Если возникли проблемы:
- Обращайтесь к разработчику @parhartem

Приятного использования!
"""
    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню",
        reply_markup=get_main_keyboard()
    )

async def back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

# Конвертер
async def start_converter(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите валюту, которую хотите конвертировать (например: BTC):",
        reply_markup=get_converter_keyboard()
    )
    await state.set_state(ConverterStates.waiting_for_currency1)

async def converter_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_currency1(message: types.Message, state: FSMContext):
    currency1 = message.text.strip().upper()
    await state.update_data(currency1=currency1)
    await message.answer("Введите количество:", reply_markup=get_converter_keyboard())
    await state.set_state(ConverterStates.waiting_for_amount)

async def converter_amount_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_amount(message: types.Message, state: FSMContext):
    if message.text == "↩️ На главный":
        await main_menu(message, state)
        return
    
    try:
        amount = float(message.text.strip())
        await state.update_data(amount=amount)
        await message.answer("В какую валюту нужно конвертировать?", reply_markup=get_converter_keyboard())
        await state.set_state(ConverterStates.waiting_for_currency2)
    except ValueError:
        await message.answer(
            "Ошибка. Пожалуйста, введите число.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

async def converter_currency2_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_currency2(message: types.Message, state: FSMContext):
    if message.text == "↩️ На главный":
        await main_menu(message, state)
        return
    
    currency2 = message.text.strip().upper()
    user_data = await state.get_data()
    
    currency1 = user_data.get('currency1')
    amount = user_data.get('amount')
    
    result = await convert_currency(currency1, amount, currency2)
    
    if result:
        await message.answer(
            f"{amount} {currency1} = {result:.2f} {currency2}",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Данные некорректны, попробуйте снова.",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()

# Избранное
async def show_favorites(message: types.Message):
    favorites = await get_favorites_with_positions(message.from_user.id)
    
    response = "Ваши избранные пары:\n\n"
    has_favorites = False
    
    for pos, cur1, cur2 in favorites:
        if cur1 and cur2:
            rate = await convert_currency(cur1, 1, cur2)
            if rate:
                response += f"{pos}. 1 {cur1} = {rate:.2f} {cur2}\n"
                has_favorites = True
            else:
                response += f"{pos}. {cur1} -> {cur2} (ошибка получения курса)\n"
                has_favorites = True
        else:
            response += f"{pos}. -\n"
    
    if not has_favorites:
        response += "Список пуст."
    
    await message.answer(response, reply_markup=get_favorites_keyboard())

async def edit_favorites_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите номер строки, которую хотите изменить",
        reply_markup=get_edit_favorites_keyboard()
    )
    await state.set_state(FavoriteStates.waiting_for_edit_choice)

async def edit_fav_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_edit_choice(message: types.Message, state: FSMContext):
    if message.text in ['1', '2', '3', '4', '5']:
        position = int(message.text)
        await state.update_data(position=position)
        await message.answer("Введите валюту 1:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(FavoriteStates.waiting_for_fav_currency1)
    elif message.text == "↩️ На главный":
        await main_menu(message, state)
    else:
        await message.answer("Пожалуйста, выберите номер от 1 до 5")

async def fav_currency1_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_fav_currency1(message: types.Message, state: FSMContext):
    if message.text == "↩️ На главный":
        await main_menu(message, state)
        return
    
    currency1 = message.text.strip().upper()
    await state.update_data(currency1=currency1)
    await message.answer("Введите валюту 2:")
    await state.set_state(FavoriteStates.waiting_for_fav_currency2)

async def fav_currency2_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_fav_currency2(message: types.Message, state: FSMContext):
    if message.text == "↩️ На главный":
        await main_menu(message, state)
        return
    
    currency2 = message.text.strip().upper()
    user_data = await state.get_data()
    
    position = user_data.get('position')
    currency1 = user_data.get('currency1')
    
    # Проверяем, что пару можно конвертировать
    test_rate = await convert_currency(currency1, 1, currency2)
    
    if test_rate:
        await update_favorite(message.from_user.id, position, currency1, currency2)
        
        # Показываем обновленный список
        favorites = await get_favorites_with_positions(message.from_user.id)
        response = "Список изменен!\n\nОбновленные пары:\n"
        for pos, cur1, cur2 in favorites:
            if cur1 and cur2:
                rate = await convert_currency(cur1, 1, cur2)
                if rate:
                    response += f"{pos}. 1 {cur1} = {rate:.2f} {cur2}\n"
                else:
                    response += f"{pos}. {cur1} -> {cur2} (ошибка)\n"
            else:
                response += f"{pos}. -\n"
        
        await message.answer(response, reply_markup=get_main_keyboard())
    else:
        await message.answer(
            "Данные некорректны, попробуйте снова.",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()

# Уведомления
async def notifications_menu(message: types.Message):
    notifications = await get_notifications_by_user(message.from_user.id)
    
    if notifications:
        response = "Ваши активные уведомления:\n\n"
        for asset, percent in notifications:
            response += f"• {asset}: изменение на {percent}%\n"
        await message.answer(response, reply_markup=get_notifications_keyboard())
    else:
        await message.answer(
            "У вас нет активных уведомлений.",
            reply_markup=get_notifications_keyboard()
        )

async def create_notification_start(message: types.Message, state: FSMContext):
    await message.answer("Введите интересующий актив (например: BTC):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(NotificationStates.waiting_for_asset)

async def notification_asset_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_notification_asset(message: types.Message, state: FSMContext):
    if message.text == "↩️ На главный":
        await main_menu(message, state)
        return
    
    asset = message.text.strip().upper()
    
    # Проверяем, существует ли такой актив
    price = await get_price_from_bybit(f"{asset}USDT")
    
    if price:
        await state.update_data(asset=asset)
        await message.answer("Введите процент изменения (например: 5 или 2.5):")
        await state.set_state(NotificationStates.waiting_for_percent)
    else:
        await message.answer(
            "Актив не найден. Пожалуйста, введите корректный актив.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

async def notification_percent_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_notification_percent(message: types.Message, state: FSMContext):
    if message.text == "↩️ На главный":
        await main_menu(message, state)
        return
    
    try:
        percent = float(message.text.strip())
        if percent <= 0:
            raise ValueError
        
        user_data = await state.get_data()
        asset = user_data.get('asset')
        
        await add_notification(message.from_user.id, asset, percent)
        await message.answer(
            f"Уведомление создано!\nАктив: {asset}\nПроцент изменения: {percent}%",
            reply_markup=get_main_keyboard()
        )
    
    except ValueError:
        await message.answer(
            "Некорректный процент. Пожалуйста, попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()

# Удаление уведомлений
async def delete_notification_start(message: types.Message, state: FSMContext):
    notifications = await get_notifications_by_user(message.from_user.id)
    
    if notifications:
        response = "Введите название актива для удаления:\n\nВаши активные уведомления:\n"
        for asset, percent in notifications:
            response += f"• {asset}: изменение на {percent}%\n"
        await message.answer(response, reply_markup=ReplyKeyboardRemove())
        await state.set_state(NotificationStates.waiting_for_delete_asset)
    else:
        await message.answer(
            "У вас нет активных уведомлений для удаления.",
            reply_markup=get_notifications_keyboard()
        )

async def delete_notification_back_to_main(message: types.Message, state: FSMContext):
    await main_menu(message, state)

async def process_delete_notification(message: types.Message, state: FSMContext):
    if message.text == "↩️ На главный":
        await main_menu(message, state)
        return
    
    asset = message.text.strip().upper()
    
    # Проверяем, существует ли такое уведомление
    notifications = await get_notifications_by_user(message.from_user.id)
    asset_exists = any(a == asset for a, _ in notifications)
    
    if asset_exists:
        await delete_notification_db(message.from_user.id, asset)
        await message.answer(
            f"Уведомление для актива {asset} удалено.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            f"Уведомление для актива {asset} не найдено.",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()

async def unknown_command(message: types.Message):
    if message.text in ["↩️ Назад", "Назад"]:
        await main_menu(message, None)
    else:
        await message.answer(
            "Ошибка. Попробуйте снова.",
            reply_markup=get_main_keyboard()
        )

# Утилиты для работы с уведомлениями (чтобы избежать конфликта имен)
async def delete_notification_db(user_id: int, asset: str):
    from database import delete_notification as db_delete_notification
    return await db_delete_notification(user_id, asset)
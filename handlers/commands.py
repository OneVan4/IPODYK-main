import asyncio
import logging
import sqlite3
from bot import bot
from WB_PARSER import GET_PRICE
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

from data.database import Database
from handlers.price_tracker import PriceTracker
from keyboards.reply import main_menu

router = Router()
pt = PriceTracker()
db = Database("data/products.db")

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("""📖 Инструкция для пользователя PriceTrackerBot

Этот бот помогает отслеживать цены на товары с Ozon и Wildberries, чтобы находить лучшие предложения. Следуйте шагам ниже для удобного использования:

1️⃣ Запуск бота:
Найдите бота в Telegram по его имени или ссылке.
Нажмите кнопку "Старт", чтобы активировать бота.
Ознакомьтесь с доступными командами.


2️⃣ Добавление товара для отслеживания:
Скопируйте ссылку на товар с сайта Ozon или Wildberries.

Отправьте команду:
/add [ссылка на товар]

Пример:
/add https://www.ozon.ru/product/example

Бот начнет следить за ценой и уведомит вас при снижении.


3️⃣ Удаление товара
Если больше не хотите отслеживать товар:

Введите команду
 /remove.

Выберите товар из списка или укажите его ID.
Подтвердите удаление.


4️⃣ Просмотр списка отслеживаемых товаров
Чтобы увидеть свои товары:

Отправьте команду
 /mylist.

Вы получите список всех отслеживаемых товаров с текущими ценами и минимальными зарегистрированными.
Нажмите на товар для получения подробностей.


5️⃣ Редактирование параметров отслеживания
Хотите настроить оповещения или задать минимальную цену?

Введите команду
 /edit.

Выберите товар, параметры которого нужно изменить.
Укажите:
Минимальную цену для уведомления.
Частоту обновлений (по умолчанию — ежедневно).

6️⃣ График изменения цен
Чтобы увидеть динамику цен:

Введите команду 
/graph.

Выберите товар из списка.
Бот отправит вам график с историей изменений цен за весь период наблюдения.


7️⃣ Уведомления

Бот отправляет уведомления при снижении цены ниже минимальной, заданной вами.
Вы можете включить или отключить уведомления через команду 
/edit.


8️⃣ Помощь
Если что-то непонятно, используйте команду 
/help
чтобы получить краткий гайд или свяжитесь с поддержкой через бота.

💸 Начните экономить прямо сейчас! Добавьте первый товар и следите за выгодными предложениями!""",
        reply_markup = main_menu
    )


@router.message(Command("add"))
async def add_product(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Пожалуйста, отправьте команду в формате /add \'ссылка на товар\'")
        return
    url = args[1]
    product_id = await db.add_product(url, message.from_user.id)
    if product_id:
        await message.reply(f"✅ Товар добавлен для отслеживания. ID: {hbold(product_id)}")
    else:
        await message.reply("❌ Не удалось добавить товар. Проверьте ссылку и попробуйте снова.")


@router.message(Command("mylist"))
async def list_products(message: Message):
    products = await db.get_user_products(message.from_user.id)
    if not products:
        await message.reply("📋 Ваш список отслеживаемых товаров пуст.")
    else:
        response = "📋 Ваши отслеживаемые товары:\n"
        for p in products:
            response += f"ID: {hbold(p['id'])}, URL: {p['url']}, Текущая цена: {hbold(p['price'])} ₽\n"
        await message.reply(response)


@router.message(Command("remove"))
async def remove_product(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Пожалуйста, отправьте команду в формате /remove \'ID товара\'")
        return
    product_id = int(args[1])
    #user.id поменять на chat.id
    if await db.remove_product(product_id, message.from_user.id):
        await message.reply(f"✅ Товар с ID {hbold(product_id)} удален из отслеживания.")
    else:
        await message.reply("❌ Не удалось удалить товар. Проверьте ID и попробуйте снова.")

async def notify_price_changes():
    while True:
        for tg_user_id in await db.table_exists():
            changes = await pt.check_prices(tg_user_id[3:])
            for change in changes:
                user_id = tg_user_id[3:]
                message = (
                   f"⚠️ Цена на товар изменилась!\n"
                            f"{hbold('Товар')}: {change['url']}\n"
                            f"Старая цена: {hbold(f'{change['old_price']:.2f}')} BYN, "
                            f"Новая цена: {hbold(f'{change['new_price']:.2f}')} BYN\n"
                            f"Изменение: {hbold(change['change_percent'])}%"
                )
                await bot.send_message(user_id, message)
        await asyncio.sleep(300) 
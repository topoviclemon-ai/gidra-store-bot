import os
import secrets
import logging

from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", 10000))
BASE_URL = os.environ["RENDER_EXTERNAL_URL"]

SECRET = secrets.token_urlsafe(32)

PRODUCTS = {
    1: {"name": "Декоративные шишки", "price": 250},
    2: {"name": "Набор для творчества", "price": 450},
}

carts = {}


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("🛒 Корзина", callback_data="cart")],
        [InlineKeyboardButton("📦 Мои заказы", callback_data="orders")],
        [InlineKeyboardButton("💬 Поддержка", callback_data="support")]
    ])


async def start(update, context):
    await update.message.reply_text(
        "🌿 Добро пожаловать в GIDRA STORE!\nВыберите раздел:",
        reply_markup=menu()
    )


async def buttons(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "home":
        await query.edit_message_text(
            "🌿 GIDRA STORE\nВыберите раздел:",
            reply_markup=menu()
        )

    elif data == "catalog":
        keyboard = [
            [InlineKeyboardButton(
                f"{p['name']} — {p['price']} ₽",
                callback_data=f"add_{pid}"
            )]
            for pid, p in PRODUCTS.items()
        ]
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="home")
        ])

        await query.edit_message_text(
            "🛍 Каталог товаров:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("add_"):
        product_id = int(data.split("_")[1])
        carts.setdefault(user_id, {})
        carts[user_id][product_id] = (
            carts[user_id].get(product_id, 0) + 1
        )
        await query.message.reply_text("Товар добавлен в корзину!")

    elif data == "cart":
        cart = carts.get(user_id, {})
        total = 0
        lines = []

        for pid, quantity in cart.items():
            product = PRODUCTS[pid]
            subtotal = product["price"] * quantity
            total += subtotal
            lines.append(
                f"{product['name']} × {quantity} — {subtotal} ₽"
            )

        message = (
            "🛒 Корзина:\n\n" + "\n".join(lines)
            if lines else "🛒 Корзина пока пуста."
        )

        if cart:
            message += f"\n\nИтого: {total} ₽"

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ В меню", callback_data="home")]
            ])
        )

    elif data == "orders":
        await query.edit_message_text(
            "📦 Пока у вас нет заказов.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ В меню", callback_data="home")]
            ])
        )

    elif data == "support":
        await query.edit_message_text(
            "💬 Напишите администратору магазина.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ В меню", callback_data="home")]
            ])
        )


async def health(request):
    return web.Response(text="GIDRA STORE is running!")


async def telegram_webhook(request):
    if request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    ) != SECRET:
        raise web.HTTPForbidden()

    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)

    return web.Response(text="OK")


async def startup(app):
    await bot_app.initialize()
    await bot_app.start()

    await bot_app.bot.set_webhook(
        url=f"{BASE_URL}/telegram/{SECRET}",
        secret_token=SECRET
    )

    logging.info("GIDRA STORE started")


async def cleanup(app):
    await bot_app.stop()
    await bot_app.shutdown()


bot_app = Application.builder().token(TOKEN).build()
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(buttons))

web_app = web.Application()
web_app.router.add_get("/", health)
web_app.router.add_post("/telegram/{secret}", telegram_webhook)

web_app.on_startup.append(startup)
web_app.on_cleanup.append(cleanup)

if __name__ == "__main__":
    web.run_app(web_app, host="0.0.0.0", port=PORT)

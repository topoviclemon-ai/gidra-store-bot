
import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 2025497608

PRODUCTS = {
    1: {"name": "Декоративные шишки", "price": 250, "unit": "набор"},
    2: {"name": "Набор для творчества", "price": 450, "unit": "набор"},
}

carts = {}

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("🛒 Корзина", callback_data="cart")],
        [InlineKeyboardButton("📦 Мои заказы", callback_data="orders")],
        [InlineKeyboardButton("💬 Поддержка", callback_data="support")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 Добро пожаловать в GIDRA STORE!\n\nВыберите раздел:",
        reply_markup=main_keyboard()
    )

async def catalog(query):
    buttons = []
    for product_id, product in PRODUCTS.items():
        buttons.append([
            InlineKeyboardButton(
                f"{product['name']} — {product['price']} ₽",
                callback_data=f"add_{product_id}"
            )
        ])
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="home")])
    await query.edit_message_text(
        "🛍 Каталог товаров\n\nВыберите товар:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_cart(query, user_id):
    cart = carts.get(user_id, {})
    if not cart:
        text = "🛒 Ваша корзина пока пуста."
    else:
        text = "🛒 Ваша корзина:\n\n"
        total = 0
        for product_id, quantity in cart.items():
            product = PRODUCTS[product_id]
            subtotal = product["price"] * quantity
            total += subtotal
            text += f"{product['name']} × {quantity} — {subtotal} ₽\n"
        text += f"\nИтого: {total} ₽"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ В меню", callback_data="home")]
        ])
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "home":
        await query.edit_message_text(
            "🌿 GIDRA STORE\n\nВыберите раздел:",
            reply_markup=main_keyboard()
        )

    elif data == "catalog":
        await catalog(query)

    elif data == "cart":
        await show_cart(query, user_id)

    elif data.startswith("add_"):
        product_id = int(data.split("_")[1])
        carts.setdefault(user_id, {})
        carts[user_id][product_id] = carts[user_id].get(product_id, 0) + 1
        await query.answer("Товар добавлен в корзину!", show_alert=True)

    elif data == "orders":
        await query.edit_message_text(
            "📦 Ваших заказов пока нет.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ В меню", callback_data="home")]
            ])
        )

    elif data == "support":
        await query.edit_message_text(
            "💬 По вопросам заказа обратитесь к администратору магазина.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ В меню", callback_data="home")]
            ])
        )

async def main():
    if not TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в настройках окружения")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

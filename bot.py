import sqlite3
import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8633118073:AAHf-Xdr-2lLaFCPNDb6cqc_tRW0xS_DY4A"
ADMIN_ID = 5718222148
SUPPORT_USERNAME = "@resistor_official"
YOUR_PHONE = "+7 918 041-39-17"

logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        address TEXT,
        phone TEXT,
        total INTEGER,
        status TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def save_order(user_id, username, full_name, address, phone, total):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''INSERT INTO orders (user_id, username, full_name, address, phone, total, status, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, username, full_name, address, phone, total, 'new', datetime.now().isoformat()))
    conn.commit()
    order_id = c.lastrowid
    conn.close()
    return order_id

def get_user_orders(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT id, total, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
    orders = c.fetchall()
    conn.close()
    return orders

init_db()

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 Купить PicoPwn", callback_data="buy")],
        [InlineKeyboardButton("📄 Описание", callback_data="description")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data="support")],
        [InlineKeyboardButton("🛍 Мои заказы", callback_data="my_orders")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context):
    await update.message.reply_text(
        "🦎 Добро пожаловать в магазин PicoPwn!\n\nВыберите действие:",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user
    
    if data == "buy":
        await query.edit_message_text(
            "🛒 Оформление заказа\n\nВведите ваше имя и фамилию:"
        )
        context.user_data['step'] = 'name'
        return
    
    elif data == "description":
        await query.edit_message_text(
            "🦎 PicoPwn — карманный кибер-девайс\n\n"
            "Функции:\n"
            "• Bluetooth Jammer — глушилка Bluetooth\n"
            "• BLE Spam — атака на iPhone/Android\n"
            "• IR HACK / BLAST — запись и отправка ИК-команд\n"
            "• Wi-Fi атаки — Deauth, Beacon Flood",
            reply_markup=main_menu()
        )
        return
    
    elif data == "support":
        await query.edit_message_text(
            f"🆘 Поддержка\n\nПо вопросам заказа и оплаты:\n\nТелефон: {YOUR_PHONE}\nПоддержка: {SUPPORT_USERNAME}\n\nВремя ответа: 10:00 - 22:00 МСК",
            reply_markup=main_menu()
        )
        return
    
    elif data == "my_orders":
        orders = get_user_orders(user.id)
        if not orders:
            await query.edit_message_text("📭 Мои заказы\n\nУ вас пока нет заказов.", reply_markup=main_menu())
        else:
            text = "📦 Ваши заказы:\n\n"
            for o in orders:
                if o[2] == "new":
                    status = "Новый"
                elif o[2] == "paid":
                    status = "Оплачен"
                else:
                    status = "Отправлен"
                text += f"Заказ #{o[0]} — {o[1]} ₽ — {status}\n   {o[3][:10]}\n\n"
            await query.edit_message_text(text, reply_markup=main_menu())
        return

async def handle_message(update: Update, context):
    user = update.effective_user
    text = update.message.text.strip()
    step = context.user_data.get('step')
    
    if not step:
        return
    
    if step == 'name':
        if len(text) < 3:
            await update.message.reply_text("Имя должно содержать минимум 3 символа. Введите имя и фамилию:")
            return
        context.user_data['full_name'] = text
        context.user_data['step'] = 'address'
        await update.message.reply_text("📍 Введите ваш адрес доставки:")
        return
    
    elif step == 'address':
        if len(text) < 5:
            await update.message.reply_text("Адрес должен содержать минимум 5 символов. Введите адрес:")
            return
        context.user_data['address'] = text
        context.user_data['step'] = 'phone'
        await update.message.reply_text("📞 Введите ваш номер телефона:")
        return
    
    elif step == 'phone':
        phone_clean = re.sub(r'[\s\-\(\)]', '', text)
        if not re.match(r'^[\+]?[0-9]{10,15}$', phone_clean):
            await update.message.reply_text("Некорректный номер телефона. Введите номер:")
            return
        
        context.user_data['phone'] = text
        
        full_name = context.user_data.get('full_name', '')
        address = context.user_data.get('address', '')
        phone = context.user_data.get('phone', '')
        
        order_id = save_order(user.id, user.username, full_name, address, phone, 5000)
        
        admin_message = (
            f"🆕 НОВЫЙ ЗАКАЗ #{order_id}\n\n"
            f"Имя: {full_name}\n"
            f"Адрес: {address}\n"
            f"Телефон: {phone}\n"
            f"Юзер: @{user.username or user.id}\n"
            f"Сумма: 5000 ₽"
        )
        
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
            print(f"Уведомление отправлено админу {ADMIN_ID}")
        except Exception as e:
            print(f"Ошибка: {e}")
        
        await update.message.reply_text(
            f"✅ ЗАКАЗ #{order_id} ОФОРМЛЕН!\n\n"
            f"Товар: PicoPwn\n"
            f"Сумма: 5000 ₽\n\n"
            f"💳 ОПЛАТА НА ОЗОН БАНК:\n"
            f"В СУММУ ВХОДИТ ДОСТАВКА:\n"
            f"Переведите 5000 ₽ на номер:\n"
            f"{YOUR_PHONE}\n\n"
            f"📌 После оплаты отправьте чек в поддержку: {SUPPORT_USERNAME}\n\n"
            f"Спасибо за заказ!",
            reply_markup=main_menu()
        )
        
        context.user_data.clear()

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Бот запущен!")
    print(f"Админ ID: {ADMIN_ID}")
    print(f"Номер для оплаты: {YOUR_PHONE}")
    app.run_polling()

if __name__ == "__main__":
    main()
import requests
import urllib3
import json
import socket
from http import HTTPStatus
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler


# 🔐 Безопаснее хранить в переменной окружения или в отдельном файле
BOT_TOKEN = "8103847969:AAE-V__8Kg2nxnL2gA3WCgLx8sk8gkK79II"
ALLOWED_CHAT_ID = 678885516

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_domains():
    with open('./domains.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("domains", [])

def get_status_description(status_code):
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "UNAVAILABLE"

def check_domain(domain):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cache-Control": "no-cache"
    }
    try:
        response = requests.get(
            f"https://{domain}", headers=headers,
            timeout=10, allow_redirects=True, verify=False
        )
        return response.status_code
    except requests.RequestException:
        return 0


async def send_default_button(application):
    chat_id = ALLOWED_CHAT_ID
    keyboard = [[InlineKeyboardButton("🔍 Проверить домены", callback_data="run_check")]]
    markup = InlineKeyboardMarkup(keyboard)
    await application.bot.send_message(chat_id=chat_id, text="Нажмите кнопку для проверки:", reply_markup=markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "run_check":
        await check_domains(update, context)


async def check_domains(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return await update.message.reply_text("Access denied.")

    loading_message = await update.message.reply_text("⏳ Проверяю доступность доменов... Пожалуйста, подождите )")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = [f"=== Проверка от {now} ==="]

    domains = load_domains()
    has_errors = False
    
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror:
            ip = "IP не найден"

        status = check_domain(domain)
        description = get_status_description(status)
        status_str = f"{status:03d} {description}"
        output.append(f"{domain} ({ip}) — {status_str}")
        if not (200 <= status < 400):
            has_errors = True

    if not has_errors:
        output.append("Ошибок не обнаружено ✅")

    result = "\n".join(output)
    await loading_message.edit_text(f"<pre>{result}</pre>", parse_mode="HTML")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(send_default_button).build()

    app.add_handler(CommandHandler("check", check_domains))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url="https://chech-pbn-bot-1.onrender.com"
    )

if __name__ == "__main__":
    main()




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
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import ssl

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

def get_ssl_expiry(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expiry = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                return expiry
    except Exception as e:
        return None



async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "run_check_crypto":
        await check_domains(update, context, source_file="domains.json")
    elif query.data == "run_check_odds":
        await check_domains(update, context, source_file="odds_domains.json")
    elif query.data == "run_check_polish":
        await check_domains(update, context, source_file="polish_domains.json")

        
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if update.effective_chat.id != ALLOWED_CHAT_ID:
    #     return await update.message.reply_text("Access denied.")

    

    keyboard = [
        [InlineKeyboardButton("🔍 Check Crypto PBN", callback_data="run_check_crypto")],
        [InlineKeyboardButton("🔍 Check Odds PBN", callback_data="run_check_odds")],
        [InlineKeyboardButton("🔍 Check Polish PBN", callback_data="run_check_polish")]
    ]




    
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите группу доменов для проверки:", reply_markup=markup)


def load_domains(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("domains", [])

async def check_domains(update: Update, context: ContextTypes.DEFAULT_TYPE, source_file="domains.json"):
    # if update.effective_chat.id != ALLOWED_CHAT_ID:
    #     return await update.message.reply_text("Access denied.")


    # Определим, откуда пришло сообщение
    if update.message:
        loading_message = await update.message.reply_text("⏳ Проверяю доступность доменов... Пожалуйста, подождите )")
    elif update.callback_query:
        await update.callback_query.answer()
        loading_message = await update.callback_query.message.reply_text("⏳ Проверяю доступность доменов... Пожалуйста, подождите )")
    else:
        return
        
    now = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")
    output = [
        f"=== Проверка от {now} ===",
        "------------------------------"
    ]

    domains = load_domains(source_file)
    has_errors = False
    errors = []
    
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror:
            ip = "IP не найден"

        status = check_domain(domain)
        description = get_status_description(status)
        status_str = f"{status:03d} {description}"
        # output.append(f"{domain} ({ip}) — {status_str}")
        expiry = get_ssl_expiry(domain)
        if expiry:
            days_left = (expiry - datetime.utcnow()).days
            ssl_status = f"🔒 SSL истекает через {days_left} дн." if days_left > 0 else "❌ SSL истёк"
        else:
            ssl_status = "❌ Нет SSL"

    output.append(f"{domain} ({ip}) — {status_str} | {ssl_status}")

        if not (200 <= status < 400):
            has_errors = True
            errors.append(f"{domain} ({ip}) — {status_str}")
            
    output.append("------------------------------")
    output.append(f"🔢 Проверено доменов: {len(domains)}")
    
    if has_errors:
        output.append("------------------------------")
        output.append("❗ Обнаружены ошибки:")
        output.extend(errors)
    else:
        output.append("------------------------------")
        output.append("Ошибок не обнаружено ✅")

    result = "\n".join(output)
    # await loading_message.edit_text(f"<pre>{result}</pre>", parse_mode="HTML")

    keyboard = [
        [InlineKeyboardButton("🔍 Check Crypto PBN", callback_data="run_check_crypto")],
        [InlineKeyboardButton("🔍 Check Odds PBN", callback_data="run_check_odds")],
        [InlineKeyboardButton("🔍 Check Polish PBN", callback_data="run_check_polish")]
    ]

    markup = InlineKeyboardMarkup(keyboard)
    await loading_message.edit_text(
        f"<pre>{result}</pre>",
        parse_mode="HTML",
        reply_markup=markup
    )    

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", start))

    
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url="https://chech-pbn-bot-1.onrender.com"
    )

if __name__ == "__main__":
    main()




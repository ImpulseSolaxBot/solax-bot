import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Загружаем переменные окружения
BOT_TOKEN = os.environ.get("8035038086:AAFtzYaBe7geXSkkZnW4zMzu3OpEc5QxacU")
SOLAX_TOKEN = os.environ.get("202505131356118907804314")
SOLAX_SN = os.environ.get("XB4050K7563064")

# Функция запроса данных у SolaX
def get_inverter_data():
    url = f"https://global.solaxcloud.com:9443/proxy/api/getRealtimeInfo.do?tokenId={SOLAX_TOKEN}&sn={SOLAX_SN}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        if not result.get("success"):
            return {"Ошибка": result.get("exception", "Неизвестная ошибка")}
        data = result.get("result", {})
        return {
            "Мощность (Вт)": data.get("acpower", "N/A"),
            "Сегодня (кВт·ч)": data.get("yieldtoday", "N/A"),
            "Всего (кВт·ч)": data.get("yieldtotal", "N/A"),
            "В сеть (Вт)": data.get("feedinpower", "N/A")
        }
    except Exception as e:
        return {"Ошибка": str(e)}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь /status чтобы получить данные инвертора.")

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_inverter_data()
    message = "\n".join([f"{key}: {value}" for key, value in data.items()])
    await update.message.reply_text("📊 Данные инвертора:\n" + message)

# Запуск бота
def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()

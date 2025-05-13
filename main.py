import telegram
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import json
import os
import time
import schedule
from threading import Thread, Event

# --- Получение переменных окружения ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SOLAX_TOKEN_ID = os.environ.get("SOLAX_TOKEN_ID")
SOLAX_SERIAL_NUMBER = os.environ.get("SOLAX_SERIAL_NUMBER")
API_URL = f"https://www.solaxcloud.com/proxyApp/proxy/api/getRealtimeInfo.do?tokenId={SOLAX_TOKEN_ID}&sn={SOLAX_SERIAL_NUMBER}"
UPDATE_INTERVAL = 60  # Интервал обновления данных в секундах
stop_event = Event()
latest_data = None

def fetch_solax_data():
    """Получает данные с API SolaxCloud и обновляет глобальную переменную."""
    global latest_data
    if not SOLAX_TOKEN_ID or not SOLAX_SERIAL_NUMBER:
        print("Ошибка: Отсутствуют переменные окружения SOLAX_TOKEN_ID или SOLAX_SERIAL_NUMBER.")
        return None
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        if data and data.get("success"):
            latest_data = data.get("result")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Данные Solax успешно обновлены.")
        else:
            print(f"Ошибка получения данных Solax: {data.get('info')}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения к API Solax: {e}")
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON от Solax.")
    return latest_data

def run_scheduler():
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def start(update: telegram.Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот для получения данных с вашего инвертора SolaX. Используйте команду /data для получения текущих данных.")

def get_inverter_data(update: telegram.Update, context: CallbackContext):
    """Отправляет текущие данные об инверторе в Telegram."""
    global latest_data
    if latest_data:
        formatted_data = json.dumps(latest_data, indent=4)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Текущие данные:\n\n{formatted_data}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Данные еще не получены или произошла ошибка.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Ошибка: Отсутствует переменная окружения TELEGRAM_BOT_TOKEN.")
        return

    # Запускаем получение данных Solax при старте
    fetch_solax_data()

    # Планируем периодическое обновление данных Solax
    schedule.every(UPDATE_INTERVAL).seconds.do(fetch_solax_data)

    # Запускаем планировщик в отдельном потоке
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Создаем Updater и передаем токен бота
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    # Получаем диспетчера для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("data", get_inverter_data))

    # Запускаем бота
    updater.start_polling()

    # Держим бота активным до получения сигнала остановки
    updater.idle()

    # Останавливаем планировщик при завершении приложения
    stop_event.set()
    scheduler_thread.join()

if __name__ == '__main__':
    main()

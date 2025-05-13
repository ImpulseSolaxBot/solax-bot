import telegram
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import json
import os
import schedule
import time
from threading import Thread, Event
import logging

# --- Получение переменных окружения ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")  # Токен вашего Telegram-бота
SOLAX_TOKEN_ID = os.environ.get("SOLAX_TOKEN_ID")  # Токен API SolaX Cloud
SOLAX_WIFI_SN = os.environ.get("SOLAX_WIFI_SN")  # Wi-Fi серийный номер инвертора
API_URL = "https://global.solaxcloud.com/api/v2/dataAccess/realtimeInfo/get"  # URL API SolaX (ЗАМЕНИТЕ <URL>!) [cite: 30]
UPDATE_INTERVAL = 60  # Интервал обновления данных (в секундах)
stop_event = Event()
latest_data = None  # Переменная для хранения последних полученных данных

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO,  # Уровень логирования (INFO, DEBUG, WARNING, ERROR)
                    format='%(asctime)s - %(levelname)s - %(message)s')  # Формат сообщений логирования

def fetch_solax_data():
    """Получает данные с API SolaxCloud и обновляет глобальную переменную latest_data."""
    global latest_data
    if not SOLAX_TOKEN_ID or not SOLAX_WIFI_SN:  # Проверка наличия необходимых переменных окружения
        logging.error("Ошибка: Отсутствуют переменные окружения SOLAX_TOKEN_ID или SOLAX_WIFI_SN.")
        return None
    try:
        headers = {'tokenld': SOLAX_TOKEN_ID}  # Помещаем токен в заголовок запроса [cite: 20]
        payload = {"wifiSn": SOLAX_WIFI_SN}  # Формируем тело запроса с wifiSn [cite: 30]
        response = requests.post(API_URL, headers=headers, json=payload)  # Выполняем POST-запрос [cite: 30]
        response.raise_for_status()  # Проверяем статус ответа (вызывает исключение при ошибке)
        data = response.json()  # Преобразуем ответ в формат JSON
        if data and data.get("success"):  # Проверяем, успешен ли запрос
            latest_data = data.get("result")  # Сохраняем полученные данные
            logging.info(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Данные Solax успешно обновлены.")
        else:
            logging.error(f"Ошибка получения данных Solax: {data.get('exception') or data}")  # Выводим сообщение об ошибке из ответа API [cite: 34]
    except requests.exceptions.RequestException as e:  # Обработка ошибок, связанных с запросом
        logging.error(f"Ошибка подключения к API Solax: {e}")
    except json.JSONDecodeError:  # Обработка ошибок декодирования JSON
        logging.error("Ошибка декодирования JSON от Solax.")
    except Exception as e:  # Обработка любых других ошибок
        logging.error(f"Произошла непредвиденная ошибка: {e}")
    return latest_data

def run_scheduler():
    """Запускает планировщик schedule в отдельном потоке."""
    while not stop_event.is_set():  # Работает, пока не установлен флаг остановки
        schedule.run_pending()  # Запускает задачи, которые должны быть выполнены
        time.sleep(1)  # Пауза в 1 секунду

def start(update: telegram.Update, context: CallbackContext):
    """Обработчик команды /start."""
    context.bot.send_message(chat_id=update.effective_chat.id,  # Отправляет сообщение в чат
                             text="Привет! Я бот для получения данных с вашего инвертора SolaX. Используйте команду /data для получения текущих данных.")

def get_inverter_data(update: telegram.Update, context: CallbackContext):
    """Обработчик команды /data. Отправляет данные об инверторе."""
    global latest_data
    if latest_data:  # Если есть данные
        formatted_data = json.dumps(latest_data, indent=4, ensure_ascii=False)  # Форматируем JSON для красивого вывода
        context.bot.send_message(chat_id=update.effective_chat.id,  # Отправляем отформатированные данные
                                 text=f"Текущие данные:\n\n{formatted_data}")
    else:  # Если данных нет
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Данные еще не получены или произошла ошибка.")

def main():
    """Основная функция для запуска бота."""
    if not TELEGRAM_BOT_TOKEN:  # Проверка наличия токена Telegram-бота
        logging.error("Ошибка: Отсутствует переменная окружения TELEGRAM_BOT_TOKEN.")
        return

    # Запускаем получение данных Solax при старте
    fetch_solax_data()

    # Планируем периодическое обновление данных Solax
    schedule.every(UPDATE_INTERVAL).seconds.do(fetch_solax_data)

    # Запускаем планировщик в отдельном потоке
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.daemon = True  # Поток-демон (завершается вместе с основным потоком)
    scheduler_thread.start()  # Запускаем поток

    # Создаем Updater и передаем токен бота
    updater = Updater(TELEGRAM_BOT_TOKEN)  # или updater = Updater(TELEGRAM_BOT_TOKEN)

    # Получаем диспетчера для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))  # Регистрируем обработчик для команды /start
    dp.add_handler(CommandHandler("data", get_inverter_data))  # Регистрируем обработчик для команды /data

    # Запускаем бота
    updater.start_polling()  # Начинаем опрос серверов Telegram на наличие обновлений

    # Держим бота активным до получения сигнала остановки
    updater.idle()  # Блокирующий вызов, останавливает выполнение программы до прерывания

    # Останавливаем планировщик при завершении приложения
    stop_event.set()  # Устанавливаем флаг остановки
    scheduler_thread.join()  # Ждем завершения потока планировщика

if __name__ == '__main__':
    main()  # Запускаем основную функцию, если скрипт запущен напрямую

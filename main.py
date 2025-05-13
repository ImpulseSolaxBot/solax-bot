import requests
import json
import time
import schedule
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Получение переменных окружения ---
TOKEN_ID = os.environ.get("SOLAX_TOKEN_ID")
SERIAL_NUMBER = os.environ.get("SOLAX_SERIAL_NUMBER")
API_URL = f"https://www.solaxcloud.com/proxyApp/proxy/api/getRealtimeInfo.do?tokenId={TOKEN_ID}&sn={SERIAL_NUMBER}"
# --------------------------------------

def fetch_and_log_data():
    """Получает данные с API SolaxCloud и логирует их."""
    if not TOKEN_ID or not SERIAL_NUMBER:
        logging.error("Отсутствуют необходимые переменные окружения (SOLAX_TOKEN_ID или SOLAX_SERIAL_NUMBER).")
        return

    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Проверить на наличие ошибок в HTTP-ответе
        data = response.json()
        if data and data.get("success"):
            result = data.get("result")
            logging.info(f"Данные с инвертора: {json.dumps(result)}")
            # Здесь вы можете добавить код для сохранения данных в файл или базу данных (например, используя переменные окружения для настроек подключения)
        else:
            logging.error(f"Ошибка получения данных: {data.get('info')}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка подключения к API: {e}")
    except json.JSONDecodeError:
        logging.error("Ошибка декодирования JSON-ответа.")
    except Exception as e:
        logging.error(f"Произошла непредвиденная ошибка: {e}")

# Запланировать выполнение задачи (например, каждую минуту)
schedule.every(1).minutes.do(fetch_and_log_data)

if __name__ == "__main__":
    logging.info("Бот Solax запущен. Получение данных каждые 60 секунд...")
    while True:
        schedule.run_pending()
        time.sleep(1)

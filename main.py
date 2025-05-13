import requests
import json
import time
import schedule

# --- Замените эти значения на свои ---
TOKEN_ID = "ВАШ_ТОКЕН_ID"
SERIAL_NUMBER = "СЕРИЙНЫЙ_НОМЕР_ИНВЕРТОРА"
API_URL = f"https://www.solaxcloud.com/proxyApp/proxy/api/getRealtimeInfo.do?tokenId={TOKEN_ID}&sn={SERIAL_NUMBER}"
# --------------------------------------

def fetch_and_print_data():
    """Получает данные с API SolaxCloud и выводит их."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Проверить на наличие ошибок в HTTP-ответе
        data = response.json()
        if data and data.get("success"):
            result = data.get("result")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Данные с инвертора:")
            print(json.dumps(result, indent=4))
            # Здесь вы можете добавить код для сохранения данных в файл или базу данных
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка получения данных: {data.get('info')}")
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка подключения: {e}")
    except json.JSONDecodeError:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка декодирования JSON")

# Запланировать выполнение задачи (например, каждую минуту)
schedule.every(1).minutes.do(fetch_and_print_data)

if __name__ == "__main__":
    print("Бот Solax запущен. Получение данных каждые 60 секунд...")
    while True:
        schedule.run_pending()
        time.sleep(1)

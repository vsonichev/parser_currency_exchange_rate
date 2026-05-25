import pandas as pd
import requests
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv


# Настройка базового логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("script.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


# Получаем API ключ из переменных окружения
load_dotenv()

# Основные настройки
API_KEY = os.getenv("API_KEY")
API_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
BACKUP_DIR = "backups"
SAVE_DIR = "save_doc"


def fetch_currency_data():
    """Получаем данные о курсах валют от API"""
    try:
        logging.info(f"Запрос данных из API...")
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("result") == "error":
            error_type = data.get("error-type", "unknown")
            raise Exception(f"API вернул ошибку: {error_type}")

        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе к API: {e}")
        raise


def save_json_backup(data):
    """Сохраняем сырой JSON-ответ в файл"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    logging.info(f"Бекап сохранен в: {path}")


def create_dataframe(data):
    """Парсим данные в DataFrame с полями Currency | Rate_to_USD"""
    try:
        rates = data.get("conversion_rates", {})

        if not rates:
            raise ValueError("Поле 'conversion_rates' не найдено в ответе API")
        
        rows = [{"Currency (код валюты)": code, "Rate_to_USD (курс к доллару)": rate} for code, rate in rates.items()]

        df = pd.DataFrame(rows)
        logging.info(f"Данные успешно обработаны. Найдено валют: {len(df)}")
        return df
    except Exception as e:
        logging.error(f"Ошибка при обработке данных: {e}")
        raise


def save_results(df):
    """Сохраняем datafarme в .csv и .xlsx"""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    csv_path = os.path.join(SAVE_DIR, "currency_rates.csv")
    xlsx_path = os.path.join(SAVE_DIR, "currency_rates.xlsx")

    # Сохранение в файлы
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    df.to_excel(xlsx_path, index=False, engine='openpyxl')

    logging.info(f"Файлы успешно сохранены в каталог '{SAVE_DIR}'")


def main():
        logging.info("=== Старт работы скрипта ===")
        try:
            # 1. Получение
            json_data = fetch_currency_data()
            
            # 2. Бекап
            save_json_backup(json_data)
            
            # 3. Парсинг
            df = create_dataframe(json_data)
            
            # 4. Экспорт
            save_results(df)
            
            logging.info("=== Скрипт завершил работу успешно ===")
        except Exception as e:
            logging.critical(f"Работа скрипта прервана из-за ошибки: {e}")

if __name__ == "__main__":
    main()

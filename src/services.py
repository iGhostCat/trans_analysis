import json
import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.views import transactions_to_json

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)


services_logger = logging.getLogger("services")
services_file_handler = logging.FileHandler(log_dir / "views.log", encoding="utf-8", mode="w")
services_file_formatter = logging.Formatter("%(asctime)s: %(filename)s: %(funcName)s: %(levelname)s: %(message)s")
services_file_handler.setFormatter(services_file_formatter)
services_logger.addHandler(services_file_handler)
services_logger.setLevel(logging.DEBUG)


def top_categories_cashback(data_path, month, year):
    """
    Возвращает сумму кэшбэка по категориям за указанный месяц и год

    Принимает:
        data_path (.xlsx таблица): транзакции
        month (int): Номер месяца (1-12)
        year (int): Год

    Возвращает:
        dict: Словарь {категория: сумма_кэшбэка}
    """
    services_logger.info("Вызов функции, начало работы")
    data_df = pd.read_excel(data_path, sheet_name="Отчет по операциям", header=0)
    # Конвертируем даты в datetime, если они еще не в этом формате
    services_logger.info("Конвертация дат в формат datetime")
    if not pd.api.types.is_datetime64_any_dtype(data_df["Дата операции"]):
        data_df["Дата операции"] = pd.to_datetime(data_df["Дата операции"], dayfirst=True)

    # Фильтруем данные по месяцу и году
    filtered_df = data_df[(data_df["Дата операции"].dt.month == month) & (data_df["Дата операции"].dt.year == year)]

    # Группируем по категориям и суммируем кэшбэк
    cashback_by_category = filtered_df.groupby("Категория")["Кэшбэк"].sum()

    services_logger.info("Сортировка")
    # Сортируем по убыванию кэшбэка
    cashback_by_category = (
        cashback_by_category[cashback_by_category > 0].sort_values(ascending=False).round(2)  # Исключаем нулевые
    )

    # Конвертируем в словарь
    result = cashback_by_category.to_dict()
    services_logger.info("Обработка завершена успешно")
    return json.dumps(cashback_by_category.to_dict(), ensure_ascii=False, indent=2)


# print(top_categories_cashback('../data/operations.xlsx', 10, 2021))


def search_phone_numbers(data_path):
    services_logger.info("Вызов функции, начало работы")
    try:
        data_df = pd.read_excel(data_path, sheet_name="Отчет по операциям", header=0)
        phone_re = re.compile(r"(\+7|7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})")
        phone_data = []

        for _, row in data_df.iterrows():
            # Ищем все совпадения в описании
            matches = phone_re.findall(str(row["Описание"]))

            if matches:
                transaction = {
                    "date": str(row["Дата операции"]),
                    "amount": float(row["Сумма операции"]),
                    "category": str(row["Категория"]),
                    "description": str(row["Описание"]),
                    "phone_numbers": list(set(matches)),  # Уникальные номера
                }
                phone_data.append(transaction)
        return transactions_to_json(phone_data)
    except Exception as e:
        services_logger.error(f"Ошибка при поиске телефонных номеров: {str(e)}")
        return transactions_to_json([])


# print(search_phone_numbers('../data/operations.xlsx'))

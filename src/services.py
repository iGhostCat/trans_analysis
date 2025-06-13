import json
from datetime import datetime
import pandas as pd
from pathlib import Path
import logging

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)


services_logger = logging.getLogger("servics")
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
    data_df = pd.read_excel(data_path, sheet_name="Отчет по операциям", header=0)
    # Конвертируем даты в datetime, если они еще не в этом формате
    if not pd.api.types.is_datetime64_any_dtype(data_df['Дата операции']):
        data_df['Дата операции'] = pd.to_datetime(data_df['Дата операции'], dayfirst=True)

    # Фильтруем данные по месяцу и году
    filtered_df = data_df[
        (data_df['Дата операции'].dt.month == month) &
        (data_df['Дата операции'].dt.year == year)
        ]

    # Группируем по категориям и суммируем кэшбэк
    cashback_by_category = filtered_df.groupby('Категория')['Кэшбэк'].sum()

    # Сортируем по убыванию кэшбэка
    cashback_by_category = (
        cashback_by_category[cashback_by_category > 0]  # Исключаем нулевые
        .sort_values(ascending=False)
        .round(2)
    )

    # Конвертируем в словарь
    result = cashback_by_category.to_dict()

    return json.dumps(cashback_by_category.to_dict(), ensure_ascii=False, indent=2)

#print(top_categories_cashback('../data/operations.xlsx', 10, 2021))
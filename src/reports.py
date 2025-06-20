import json
import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.views import transactions_to_json

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)


reports_logger = logging.getLogger("reports")
reports_file_handler = logging.FileHandler(log_dir / "views.log", encoding="utf-8", mode="w")
reports_file_formatter = logging.Formatter("%(asctime)s: %(filename)s: %(funcName)s: %(levelname)s: %(message)s")
reports_file_handler.setFormatter(reports_file_formatter)
reports_logger.addHandler(reports_file_handler)
reports_logger.setLevel(logging.DEBUG)


def spending_by_category(database, search_category, date_of_ops=None):
    """
    Поиск транзакций по точному совпадению категории за последние 3 месяца

    :param database: Путь к файлу с транзакциями
    :param search_category: Категория для поиска (точное совпадение)
    :param date_of_ops: Опциональная дата (по умолчанию текущая дата)
    :return: JSON с найденными транзакциями
    """
    reports_logger.info("Вызов функции spending_by_category")

    try:
        # Загружаем данные
        data_df = pd.read_excel(database, sheet_name="Отчет по операциям", header=0)

        # Устанавливаем дату (текущую или переданную)
        target_date = datetime.now() if date_of_ops is None else date_of_ops
        reports_logger.info(f"Используемая дата для фильтрации: {target_date}")

        # Конвертируем даты
        data_df["Дата операции"] = pd.to_datetime(data_df["Дата операции"], dayfirst=True)

        # Вычисляем дату 3 месяца назад
        three_months_ago = target_date - pd.DateOffset(months=3)

        # Фильтруем по категории и дате
        filtered = data_df[
            (data_df["Категория"].str.strip().str.lower() == search_category.strip().lower())
            & (data_df["Дата операции"] >= three_months_ago)
            & (data_df["Дата операции"] <= target_date)
        ]

        # Форматируем результат
        results = []
        for _, row in filtered.iterrows():
            results.append(
                {
                    "date": row["Дата операции"].strftime("%d.%m.%Y"),
                    "amount": float(row["Сумма операции"]),
                    "category": row["Категория"],
                    "description": row["Описание"],
                }
            )

        return json.dumps({"transactions": results}, ensure_ascii=False, indent=4)

    except Exception as e:
        reports_logger.error(f"Ошибка в spending_by_category: {str(e)}")
        return json.dumps({"transactions": []}, ensure_ascii=False)


# print(spending_by_category("../data/operations.xlsx", "Рестораны", datetime(2021, 10, 10)))

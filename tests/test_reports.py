import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Добавляем путь к src в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Фикстура с более точными тестовыми данными
@pytest.fixture
def transactions_data():
    now = datetime.now()
    return {
        "Дата операции": [
            (now - timedelta(days=30)).strftime("%d.%m.%Y"),  # Должна попасть
            (now - timedelta(days=45)).strftime("%d.%m.%Y"),  # Должна попасть (3 месяца = 90 дней)
            (now - timedelta(days=91)).strftime("%d.%m.%Y"),  # Не должна попасть
            now.strftime("%d.%m.%Y"),  # Должна попасть
        ],
        "Категория": ["Food", "Food", "Transport", "Food"],
        "Сумма операции": [-100, -200, -300, -400],
        "Описание": ["Lunch", "Groceries", "Taxi", "Dinner"],
        "Статус": ["OK", "OK", "OK", "OK"],
    }


# Фикстура для DataFrame
@pytest.fixture
def transactions_df(transactions_data):
    df = pd.DataFrame(transactions_data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    return df


# Фикстура для мока Excel
@pytest.fixture
def mock_excel(transactions_df):
    with patch("pandas.read_excel", return_value=transactions_df) as mock:
        yield mock


# Тест успешного выполнения
def test_spending_by_category_success(mock_excel, transactions_df):
    from src.reports import spending_by_category

    with patch("src.reports.reports_logger"):
        result = spending_by_category("dummy.xlsx", "Food")
        data = json.loads(result)

        # Проверяем количество найденных транзакций
        assert len(data["transactions"]) == 3
        # Проверяем что read_excel вызывался ровно 1 раз
        mock_excel.assert_called_once_with("dummy.xlsx", sheet_name="Отчет по операциям", header=0)


# Тест с указанием даты
def test_spending_by_category_with_date(mock_excel, transactions_df):
    from src.reports import spending_by_category

    test_date = datetime.now() - timedelta(days=40)
    with patch("src.reports.reports_logger"):
        result = spending_by_category("dummy.xlsx", "Food", test_date)
        data = json.loads(result)

        # Должна быть только 1 операция (45 дней назад)
        assert len(data["transactions"]) == 1
        assert data["transactions"][0]["description"] == "Groceries"


# Остальные тесты остаются без изменений...

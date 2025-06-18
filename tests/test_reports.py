import json
from datetime import datetime, timedelta
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.reports import spending_by_category


def test_spending_by_category_exact_match():
    """Тестирует точное совпадение категорий"""
    test_data = {
        "Дата операции": [
            (datetime.now() - timedelta(days=30)).strftime("%d.%m.%Y %H:%M:%S"),
            (datetime.now() - timedelta(days=60)).strftime("%d.%m.%Y %H:%M:%S"),
            "01.01.2020 12:00:00",  # Слишком старая дата
        ],
        "Сумма операции": [100, 200, 300],
        "Категория": ["Супермаркеты", "Супермаркеты", "Супермаркеты"],
        "Описание": ["Покупка 1", "Покупка 2", "Покупка 3"],
    }

    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(test_data)

        result = spending_by_category("dummy.xlsx", "Супермаркеты")
        data = json.loads(result)

        assert len(data["transactions"]) == 2
        assert all(t["category"] == "Супермаркеты" for t in data["transactions"])


def test_spending_by_category_case_insensitive():
    """Тестирует регистронезависимый поиск"""
    test_data = {
        "Дата операции": [(datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y %H:%M:%S")],
        "Сумма операции": [100],
        "Категория": ["Супермаркеты"],
        "Описание": ["Покупка"],
    }

    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(test_data)

        # Проверяем разные варианты написания
        for query in ["супермаркеты", "СУПЕРМАРКЕТЫ", " Супермаркеты "]:
            result = spending_by_category("dummy.xlsx", query)
            data = json.loads(result)
            assert len(data["transactions"]) == 1


def test_spending_by_category_date_filter():
    """Тестирует фильтрацию по дате включая граничные значения"""
    test_date = datetime(2023, 6, 15)
    test_data = {
        "Дата операции": [
            "15.05.2023 12:00:00",  # Должен попасть
            "15.03.2023 12:00:00",  # Должен попасть (ровно 3 месяца)
            "14.03.2023 12:00:00",  # Не должен попасть (> 3 месяцев)
            "10.06.2023 12:00:00",  # Должен попасть
        ],
        "Сумма операции": [100, 200, 300, 400],
        "Категория": ["Тест"] * 4,
        "Описание": ["Тест"] * 4,
    }

    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(test_data)

        result = spending_by_category("dummy.xlsx", "Тест", test_date)
        data = json.loads(result)

        assert len(data["transactions"]) == 3
        assert {t["amount"] for t in data["transactions"]} == {100.0, 200.0, 400.0}


def test_spending_by_category_no_matches():
    """Тестирует случай, когда нет совпадений"""
    test_data = {
        "Дата операции": [(datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y %H:%M:%S")],
        "Сумма операции": [100],
        "Категория": ["Другая категория"],
        "Описание": ["Покупка"],
    }

    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(test_data)

        result = spending_by_category("dummy.xlsx", "Супермаркеты")
        data = json.loads(result)

        assert data["transactions"] == []


def test_spending_by_category_file_error():
    """Тестирует обработку ошибки чтения файла"""
    with patch("pandas.read_excel", side_effect=FileNotFoundError("File not found")):
        result = spending_by_category("nonexistent.xlsx", "Тест")
        data = json.loads(result)

        assert data["transactions"] == []


def test_spending_by_category_empty_data():
    """Тестирует обработку пустого файла"""
    test_data = {"Дата операции": [], "Сумма операции": [], "Категория": [], "Описание": []}

    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(test_data)

        result = spending_by_category("dummy.xlsx", "Тест")
        data = json.loads(result)

        assert data["transactions"] == []

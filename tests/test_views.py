import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest


# Исправленный тест для transactions_to_json
def test_transactions_to_json():
    # Импортируем функцию из правильного модуля (замените 'your_module' на реальный путь)
    from src.views import transactions_to_json

    test_data = [
        {"date": datetime(2023, 1, 1, 12, 0), "amount": 100},
        {"date": datetime(2023, 1, 2, 12, 0), "amount": 200},
    ]

    with patch("src.views.views_logger") as mock_logger:
        result = transactions_to_json(test_data)
        # Проверяем что результат валидный JSON
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["amount"] == 100
        mock_logger.info.assert_called()


# Фикстура для тестов с DataFrame
@pytest.fixture
def sample_transactions_df():
    data = {
        "Статус": ["OK", "FAIL", "OK", "OK"],
        "Сумма операции": [-100, 200, -300, -400],
        "Сумма операции с округлением": [-100, 200, -300, -400],
        "Кэшбэк": [1, 0, 3, 4],
        "Номер карты": ["1234567890123456", "1234567890123456", "9876543210987654", "9876543210987654"],
        "Дата операции": [datetime.now()] * 4,
        "Категория": ["Food", "Transport", "Food", "Entertainment"],
        "Описание": ["Lunch", "Taxi", "Dinner", "Cinema"],
    }
    return pd.DataFrame(data)


# Исправленный тест для sums_by_category
def test_sums_by_category(sample_transactions_df):
    from src.views import sums_by_category

    with patch("src.views.views_logger") as mock_logger:
        result = sums_by_category(sample_transactions_df)
        assert "cards" in result
        assert len(result["cards"]) == 2  # 2 уникальных карты
        mock_logger.info.assert_called()


# Исправленный тест для top_transactions
def test_top_transactions(sample_transactions_df):
    from src.views import top_transactions

    with patch("src.views.views_logger") as mock_logger:
        result = top_transactions(sample_transactions_df)
        assert "top_transactions" in result
        assert len(result["top_transactions"]) <= 5
        mock_logger.info.assert_called()


# Исправленный тест для currency_rates_api
@patch("src.views.requests.get")
def test_currency_rates_api(mock_get):
    from src.views import currency_rates_api

    # Создаем мок ответа
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "Valute": {"USD": {"Value": 75.5, "Name": "Доллар США"}, "EUR": {"Value": 85.5, "Name": "Евро"}}
    }
    mock_get.return_value = mock_response

    # Мок файла с валютами
    file_content = '{"user_currencies": ["USD", "EUR"]}'

    with patch("builtins.open", mock_open(read_data=file_content)), patch("src.views.views_logger") as mock_logger:
        result = currency_rates_api("dummy_path.json")
        assert len(result) == 2
        assert result[0]["currency"] == "USD"
        assert result[0]["rate"] == 75.5
        mock_logger.info.assert_called()


# Исправленный тест для get_stock_prices
@patch("src.views.requests.get")
def test_get_stock_prices(mock_get):
    from src.views import get_stock_prices

    # Создаем мок ответа
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [{"price": 150.75}]
    mock_get.return_value = mock_response

    # Мок файла с акциями
    file_content = '{"user_stocks": ["AAPL", "GOOGL"]}'

    with patch("builtins.open", mock_open(read_data=file_content)), patch("src.views.views_logger") as mock_logger:
        result = get_stock_prices("dummy_path.json", "dummy_key")
        assert "stock_prices" in result
        assert len(result["stock_prices"]) == 2
        mock_logger.info.assert_called()


# Исправленный тест для page_main
@patch("src.views.pd.read_excel")
@patch("src.views.greetings")
@patch("src.views.sums_by_category")
@patch("src.views.top_transactions")
@patch("src.views.currency_rates_api")
@patch("src.views.get_stock_prices")
def test_page_main(mock_stocks, mock_currency, mock_top, mock_sums, mock_greetings, mock_read):
    from src.views import page_main

    # Настройка моков
    mock_greetings.return_value = "Добрый день!"
    mock_sums.return_value = {"cards": []}
    mock_top.return_value = {"top_transactions": []}
    mock_currency.return_value = []
    mock_stocks.return_value = {"stock_prices": []}

    mock_df = pd.DataFrame()
    mock_read.return_value = mock_df

    result = page_main("2023-01-01 12:00:00", "dummy_path.xlsx")
    result_data = json.loads(result)

    assert "greeting" in result_data
    assert "cards" in result_data
    assert "top_transactions" in result_data
    assert "currency_rates" in result_data
    assert "stock_prices" in result_data

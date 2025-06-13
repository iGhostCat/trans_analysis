import json
import os
from datetime import datetime

import pandas as pd
import pytest
import requests

from src.views import top_transactions, transactions_to_json



# Фикстура для тестов transactions_to_json
@pytest.fixture
def sample_transactions():
    """Возвращает тестовый список транзакций."""
    return [
        {
            "Дата операции": datetime(2023, 1, 1, 12, 0, 0),
            "Сумма операции": -100.50,
            "Валюта операции": "RUB",
            "Статус": "OK",
        },
        {
            "Дата операции": datetime(2023, 1, 2, 15, 30, 0),
            "Сумма операции": 200.75,
            "Валюта операции": "USD",
            "Статус": "FAILED",
        },
    ]


# Тесты для transactions_to_json
def test_transactions_to_json_returns_string(sample_transactions):
    """Проверяет, что возвращается строка JSON."""
    json_str = transactions_to_json(sample_transactions)
    assert isinstance(json_str, str)


def test_transactions_to_json_serializes_dates(sample_transactions):
    """Проверяет сериализацию дат в JSON."""
    json_str = transactions_to_json(sample_transactions)
    data = json.loads(json_str)
    assert data[0]["Дата операции"] == "2023-01-01 12:00:00"


def test_transactions_to_json_keeps_structure(sample_transactions):
    """Проверяет сохранение структуры данных."""
    json_str = transactions_to_json(sample_transactions)
    data = json.loads(json_str)
    assert data[0]["Валюта операции"] == "RUB"
    assert data[1]["Статус"] == "FAILED"


def test_top_transactions_returns_correct_format():
    """Проверяет, что функция возвращает данные в правильном формате."""
    # Подготовка тестовых данных
    test_data = pd.DataFrame(
        {
            "Дата операции": ["01.01.2022", "02.01.2022"],
            "Сумма операции": [100, -200],
            "Категория": ["Категория1", "Категория2"],
            "Описание": ["Описание1", "Описание2"],
            "Сумма операции с округлением": [100, 200],  # Используется для сортировки
        }
    )

    # Вызов функции
    result = top_transactions(test_data)

    # Проверки
    assert isinstance(result, dict)
    assert "top_transactions" in result
    assert isinstance(result["top_transactions"], list)
    assert len(result["top_transactions"]) == 2  # Т.к. в тестовых данных 2 строки

    for transaction in result["top_transactions"]:
        assert set(transaction.keys()) == {"date", "amount", "category", "description"}


def test_top_transactions_sorts_correctly():
    """Проверяет, что транзакции сортируются по убыванию суммы."""
    test_data = pd.DataFrame(
        {
            "Дата операции": ["01.01.2022", "02.01.2022", "03.01.2022"],
            "Сумма операции": [100, 300, 200],
            "Категория": ["A", "B", "C"],
            "Описание": ["A", "B", "C"],
            "Сумма операции с округлением": [100, 300, 200],
        }
    )

    result = top_transactions(test_data)
    amounts = [t["amount"] for t in result["top_transactions"]]

    # Проверяем, что суммы идут в порядке убывания
    assert amounts == [300, 200, 100]


def test_top_transactions_with_excel_example():
    """Проверяет функцию на данных из примера Excel."""
    # Создаем DataFrame, аналогичный вашему примеру
    test_data = pd.DataFrame(
        {
            "Дата операции": ["31.12.2021 16:44:00", "31.12.2021 16:42:04"],
            "Сумма операции": [-160.89, -64],
            "Категория": ["Супермаркеты", "Супермаркеты"],
            "Описание": ["Колхоз", "Колхоз"],
            "Сумма операции с округлением": [160.89, 64],
        }
    )

    result = top_transactions(test_data)

    # Проверяем, что возвращается 2 транзакции (как в примере)
    assert len(result["top_transactions"]) == 2

    # Проверяем первую транзакцию (должна быть с бóльшей суммой)
    first_transaction = result["top_transactions"][0]
    assert first_transaction["date"] == "31.12.2021 16:44:00"
    assert first_transaction["amount"] == -160.89
    assert first_transaction["category"] == "Супермаркеты"
    assert first_transaction["description"] == "Колхоз"


def test_top_transactions_empty_input():
    """Проверяет, как функция обрабатывает пустой DataFrame."""
    empty_df = pd.DataFrame(
        columns=["Дата операции", "Сумма операции", "Категория", "Описание", "Сумма операции с округлением"]
    )

    result = top_transactions(empty_df)
    assert result == {"top_transactions": []}


def test_top_transactions_limits_to_top_5():
    """Проверяет, что функция возвращает не более 5 транзакций."""
    # Создаем DataFrame с 10 транзакциями
    test_data = pd.DataFrame(
        {
            "Дата операции": [f"01.01.2022 {i}:00:00" for i in range(10)],
            "Сумма операции": [i * 100 for i in range(10)],
            "Категория": ["Категория"] * 10,
            "Описание": ["Описание"] * 10,
            "Сумма операции с округлением": [i * 100 for i in range(10)],
        }
    )

    result = top_transactions(test_data)
    assert len(result["top_transactions"]) == 5  # Должно вернуть только топ-5


import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.views import currency_rates_api  # Замените `your_module` на имя вашего модуля

# Тестовые данные
TEST_JSON_DATA = {"user_currencies": ["USD", "EUR"]}

TEST_API_RESPONSE = {
    "Valute": {
        "USD": {"Value": 73.21, "Name": "Доллар США"},
        "EUR": {"Value": 85.43, "Name": "Евро"},
        "GBP": {"Value": 98.76, "Name": "Фунт стерлингов"},
    }
}


def test_currency_rates_api_success():
    """Тестирует успешный сценарий работы функции."""
    with (
        patch("builtins.open", mock_open(read_data=json.dumps({"user_currencies": ["USD", "EUR"]}))),
        patch("requests.get") as mock_get,
    ):
        # Правильная структура ответа API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Valute": {
                "USD": {"Value": 73.21, "Name": "Доллар США"},
                "EUR": {"Value": 85.43, "Name": "Евро"},
                "GBP": {"Value": 98.76, "Name": "Фунт стерлингов"},
            }
        }
        mock_get.return_value = mock_response

        result = currency_rates_api("dummy_path.json")

        assert len(result) == 2
        assert {"currency": "USD", "rate": 73.21} in result
        assert {"currency": "EUR", "rate": 85.43} in result


def test_currency_rates_api_empty_currencies():
    """Тестирует случай, когда список валют пуст."""
    with (
        patch("builtins.open", mock_open(read_data=json.dumps({"user_currencies": []}))),
        patch("requests.get") as mock_get,
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Valute": {"USD": {"Value": 73.21, "Name": "Доллар США"}, "EUR": {"Value": 85.43, "Name": "Евро"}}
        }
        mock_get.return_value = mock_response

        result = currency_rates_api("dummy_path.json")

        assert len(result) == 2  # Должны вернуться все валюты


def test_currency_rates_api_request_error():
    """Тестирует обработку ошибки запроса к API."""
    with patch("builtins.open", mock_open(read_data=json.dumps(TEST_JSON_DATA))), patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("API недоступен")

        with pytest.raises(Exception) as exc_info:
            currency_rates_api("dummy_path.json")

        assert "Ошибка при получении курсов валют" in str(exc_info.value)


def test_currency_rates_api_invalid_json():
    """Тестирует обработку невалидного JSON в файле."""
    with patch("builtins.open", mock_open(read_data="invalid json")), pytest.raises(Exception) as exc_info:
        currency_rates_api("bad_file.json")

    assert "Ошибка обработки данных" in str(exc_info.value)


def test_currency_rates_api_missing_key():
    """Тестирует случай, когда в файле нет ключа user_currencies."""
    with patch("builtins.open", mock_open(read_data=json.dumps({}))), patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"Valute": {"USD": {"Value": 73.21, "Name": "Доллар США"}}}
        mock_get.return_value = mock_response

        result = currency_rates_api("dummy_path.json")

        assert len(result) == 1  # Должна вернуться единственная валюта


import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.views import get_stock_prices  # Замените `your_module` на имя вашего модуля

# Тестовые данные
TEST_JSON_DATA = {"user_stocks": ["AAPL", "MSFT", "GOOGL"]}

TEST_API_RESPONSE = [
    {"symbol": "AAPL", "price": 175.32},
    {"symbol": "MSFT", "price": 328.39},
    {"symbol": "GOOGL", "price": 142.56},
]


def test_get_stock_prices_success():
    """Тестирует успешный сценарий работы функции."""
    # Мокаем открытие файла и запросы к API
    with patch("builtins.open", mock_open(read_data=json.dumps(TEST_JSON_DATA))), patch("requests.get") as mock_get:
        # Настраиваем мок для requests.get
        mock_response = MagicMock()
        mock_response.json.side_effect = [
            [TEST_API_RESPONSE[0]],  # Для AAPL
            [TEST_API_RESPONSE[1]],  # Для MSFT
            [TEST_API_RESPONSE[2]],  # Для GOOGL
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Вызываем функцию
        result = get_stock_prices("dummy_path.json", "test_api_key")

        # Проверяем результат
        assert len(result["stock_prices"]) == 3
        assert {"stock": "AAPL", "price": 175.32} in result["stock_prices"]
        assert {"stock": "MSFT", "price": 328.39} in result["stock_prices"]
        assert {"stock": "GOOGL", "price": 142.56} in result["stock_prices"]

        # Проверяем, что запросы делались для каждого тикера
        assert mock_get.call_count == 3
        mock_get.assert_any_call("https://financialmodelingprep.com/api/v3/quote-short/AAPL?apikey=test_api_key")
        mock_get.assert_any_call("https://financialmodelingprep.com/api/v3/quote-short/MSFT?apikey=test_api_key")
        mock_get.assert_any_call("https://financialmodelingprep.com/api/v3/quote-short/GOOGL?apikey=test_api_key")


def test_get_stock_prices_empty_tickers():
    """Тестирует случай, когда список тикеров пуст."""
    empty_json = {"user_stocks": []}

    with patch("builtins.open", mock_open(read_data=json.dumps(empty_json))):
        result = get_stock_prices("dummy_path.json", "test_api_key")

        assert result == {"stock_prices": []}


def test_get_stock_prices_file_error():
    """Тестирует обработку ошибки при чтении файла."""
    with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
        with pytest.raises(Exception):
            get_stock_prices("nonexistent.json", "test_api_key")


def test_get_stock_prices_api_error():
    """Тестирует обработку ошибки API для одного из тикеров."""
    test_data = {"user_stocks": ["AAPL", "MSFT", "GOOGL"]}

    with patch("builtins.open", mock_open(read_data=json.dumps(test_data))), patch("requests.get") as mock_get:

        # Настраиваем разные ответы для разных тикеров
        def side_effect(url, *args, **kwargs):
            mock = MagicMock()
            if "AAPL" in url:
                mock.json.return_value = [{"symbol": "AAPL", "price": 175.32}]
            elif "GOOGL" in url:
                mock.json.return_value = [{"symbol": "GOOGL", "price": 142.56}]
            else:  # MSFT
                mock.raise_for_status.side_effect = requests.exceptions.RequestException("API error")
            return mock

        mock_get.side_effect = side_effect

        result = get_stock_prices("dummy_path.json", "test_api_key")

        assert len(result["stock_prices"]) == 2
        assert {"stock": "AAPL", "price": 175.32} in result["stock_prices"]
        assert {"stock": "GOOGL", "price": 142.56} in result["stock_prices"]


def test_get_stock_prices_invalid_response():
    """Тестирует обработку невалидного ответа API."""
    with patch("builtins.open", mock_open(read_data=json.dumps(TEST_JSON_DATA))), patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = [{}]  # Пустой словарь без нужных полей
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_stock_prices("dummy_path.json", "test_api_key")

        # Должен вернуться пустой список, так как данные невалидны
        assert result == {"stock_prices": []}


def test_get_stock_prices_missing_key():
    """Тестирует случай, когда в файле нет ключа user_stocks."""
    with patch("builtins.open", mock_open(read_data=json.dumps({}))):
        result = get_stock_prices("dummy_path.json", "test_api_key")

        assert result == {"stock_prices": []}

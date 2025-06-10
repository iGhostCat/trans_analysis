import pytest
from datetime import datetime
from src.views import excel_to_list_of_dicts, transactions_to_json
import pandas as pd
import os
import json

# Фикстура для тестов excel_to_list_of_dicts
@pytest.fixture
def sample_excel_file(tmp_path):
    """Создает временный Excel-файл для тестов."""
    file_path = tmp_path / "test_transactions.xlsx"
    data = {
        "Дата операции": ["2023-01-01 12:00:00", "2023-01-02 15:30:00"],
        "Дата платежа": ["2023-01-01", "2023-01-02"],
        "Номер карты": ["*1234", None],
        "Статус": ["OK", "FAILED"],
        "Сумма операции": [-100.50, 200.75],
        "Валюта операции": ["RUB", "USD"]
    }
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False, sheet_name="Отчет по операциям")
    return file_path

# Фикстура для тестов transactions_to_json
@pytest.fixture
def sample_transactions():
    """Возвращает тестовый список транзакций."""
    return [
        {
            "Дата операции": datetime(2023, 1, 1, 12, 0, 0),
            "Сумма операции": -100.50,
            "Валюта операции": "RUB",
            "Статус": "OK"
        },
        {
            "Дата операции": datetime(2023, 1, 2, 15, 30, 0),
            "Сумма операции": 200.75,
            "Валюта операции": "USD",
            "Статус": "FAILED"
        }
    ]

# Тесты для excel_to_list_of_dicts
def test_excel_to_list_of_dicts_loads_data(sample_excel_file):
    """Проверяет загрузку данных из Excel."""
    transactions = excel_to_list_of_dicts(sample_excel_file)
    assert len(transactions) == 2

def test_excel_to_list_of_dicts_keys_match(sample_excel_file):
    """Проверяет, что ключи соответствуют столбцам Excel."""
    transactions = excel_to_list_of_dicts(sample_excel_file)
    expected_keys = [
        "Дата операции", "Дата платежа", "Номер карты",
        "Статус", "Сумма операции", "Валюта операции"
    ]
    assert list(transactions[0].keys()) == expected_keys

def test_excel_to_list_of_dicts_handles_none(sample_excel_file):
    """Проверяет обработку None-значений."""
    transactions = excel_to_list_of_dicts(sample_excel_file)
    assert transactions[1]["Номер карты"] is None

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
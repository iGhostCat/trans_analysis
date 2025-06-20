import json
import re
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest


# Фикстура для тестовых данных транзакций
@pytest.fixture
def sample_transactions_data():
    return {
        "Дата операции": ["01.10.2021", "15.10.2021", "05.11.2021", "20.10.2021"],
        "Категория": ["Food", "Transport", "Food", "Entertainment"],
        "Кэшбэк": [10.5, 5.0, 15.2, 0.0],
        "Сумма операции": [-1000, -500, -1200, -800],
        "Описание": ["Payment for cafe +79123456789", "Taxi 8(912)345-67-89", "Restaurant", "Cinema"],
    }


# Фикстура для мока Excel файла
@pytest.fixture
def mock_excel_file(sample_transactions_data):
    with patch("pandas.read_excel") as mock_read:
        mock_read.return_value = pd.DataFrame(sample_transactions_data)
        yield mock_read


# Фикстура для логгера
@pytest.fixture
def mock_logger():
    with patch("src.services.services_logger") as mock:
        yield mock


# Тесты для функции top_categories_cashback
class TestTopCategoriesCashback:
    def test_successful_processing(self, mock_excel_file, mock_logger):
        from src.services import top_categories_cashback

        result = top_categories_cashback("dummy.xlsx", 10, 2021)
        data = json.loads(result)

        assert isinstance(data, dict)
        assert "Food" in data
        assert data["Food"] == 10.5
        mock_excel_file.assert_called_once_with("dummy.xlsx", sheet_name="Отчет по операциям", header=0)
        mock_logger.info.assert_called()

    def test_no_data_for_period(self, mock_excel_file, mock_logger):
        from src.services import top_categories_cashback

        result = top_categories_cashback("dummy.xlsx", 12, 2021)
        data = json.loads(result)

        assert data == {}
        mock_logger.info.assert_called()

    def test_date_conversion(self, mock_excel_file):
        from src.services import top_categories_cashback

        # Мокаем DataFrame с датами в строковом формате
        with patch("pandas.read_excel") as mock_read:
            test_data = {
                "Дата операции": ["01.10.2021", "02.10.2021"],
                "Категория": ["Food", "Transport"],
                "Кэшбэк": [10, 20],
                "Сумма операции": [-100, -200],
            }
            mock_read.return_value = pd.DataFrame(test_data)

            result = top_categories_cashback("dummy.xlsx", 10, 2021)
            data = json.loads(result)

            assert len(data) == 2


# Тесты для функции search_phone_numbers
class TestSearchPhoneNumbers:
    def test_phone_number_detection(self, mock_excel_file, mock_logger):
        from src.services import search_phone_numbers

        with patch("src.services.transactions_to_json") as mock_json:
            mock_json.return_value = '{"test": "data"}'
            result = search_phone_numbers("dummy.xlsx")

            assert result == '{"test": "data"}'
            mock_excel_file.assert_called_once()
            mock_logger.info.assert_called()

    def test_multiple_phone_formats(self, mock_excel_file):
        from src.services import search_phone_numbers

        # Мокаем данные с разными форматами телефонов
        test_data = {
            "Дата операции": ["01.10.2021", "02.10.2021"],
            "Категория": ["Food", "Transport"],
            "Сумма операции": [-100, -200],
            "Описание": ["Payment +7 912 345 67 89", "Refund 89123456789"],
        }

        with patch("pandas.read_excel") as mock_read:
            mock_read.return_value = pd.DataFrame(test_data)
            with patch("src.services.transactions_to_json") as mock_json:
                search_phone_numbers("dummy.xlsx")
                # Проверяем что номера были найдены
                assert mock_json.call_args[0][0][0]["phone_numbers"]

    def test_error_handling(self, mock_excel_file, mock_logger):
        from src.services import search_phone_numbers

        with patch("pandas.read_excel", side_effect=Exception("Test error")):
            with patch("src.services.transactions_to_json") as mock_json:
                mock_json.return_value = '{"transactions": []}'
                result = search_phone_numbers("invalid.xlsx")

                assert result == '{"transactions": []}'
                mock_logger.error.assert_called()


# Дополнительные тесты для проверки регулярного выражения
def test_phone_regex():
    from src.services import search_phone_numbers

    test_cases = [
        ("+79123456789", [("+7", "912", "345", "67", "89")]),
        ("89123456789", [("8", "912", "345", "67", "89")]),
        ("8(912)345-67-89", [("8", "912", "345", "67", "89")]),
        ("7 912 345 67 89", [("7", "912", "345", "67", "89")]),
        ("No phone here", []),
    ]

    phone_re = re.compile(r"(\+7|7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})")

    for text, expected in test_cases:
        assert phone_re.findall(text) == expected

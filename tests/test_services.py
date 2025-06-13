import pytest
from unittest.mock import patch, mock_open
import pandas as pd
import json
from datetime import datetime
from src.services import top_categories_cashback  # Замените your_module на имя вашего модуля

# Тестовые данные
TEST_DATA = {
    "Дата операции": ["01.10.2021 12:00", "15.10.2021 18:30", "01.11.2021 09:15"],
    "Категория": ["Супермаркеты", "Рестораны", "Супермаркеты"],
    "Кэшбэк": [1.5, 2.0, 3.0],
    "Статус": ["OK", "OK", "OK"]
}


def test_top_categories_cashback_success():
    """Тестирует успешный сценарий работы функции."""
    # Мокаем чтение Excel файла
    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(TEST_DATA)

        # Вызываем функцию для октября 2021
        result = top_categories_cashback("dummy_path.xlsx", 10, 2021)
        data = json.loads(result)

        # Проверяем результат
        assert len(data) == 2  # Должны быть 2 категории
        assert data["Супермаркеты"] == 1.5
        assert data["Рестораны"] == 2.0
        assert "Супермаркеты" in data
        assert "Рестораны" in data


def test_top_categories_cashback_no_data():
    """Тестирует случай, когда нет данных за указанный период."""
    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(TEST_DATA)

        # Вызываем для месяца, которого нет в данных
        result = top_categories_cashback("dummy_path.xlsx", 12, 2021)
        data = json.loads(result)

        assert data == {}  # Должен вернуться пустой словарь


def test_top_categories_cashback_zero_cashback():
    """Тестирует исключение категорий с нулевым кэшбэком."""
    test_data = TEST_DATA.copy()
    test_data["Кэшбэк"] = [0, 2.0, 0]  # Две операции с нулевым кэшбэком

    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(test_data)

        result = top_categories_cashback("dummy_path.xlsx", 10, 2021)
        data = json.loads(result)

        assert len(data) == 1  # Должна остаться только одна категория
        assert "Рестораны" in data
        assert data["Рестораны"] == 2.0


def test_top_categories_cashback_sorting():
    """Тестирует правильность сортировки по убыванию."""
    test_data = TEST_DATA.copy()
    test_data["Кэшбэк"] = [1.0, 3.0, 2.0]  # Разные суммы кэшбэка

    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(test_data)

        result = top_categories_cashback("dummy_path.xlsx", 10, 2021)
        data = json.loads(result)

        # Проверяем порядок категорий
        categories = list(data.keys())
        assert categories[0] == "Рестораны"  # Должен быть первым (3.0)
        assert categories[1] == "Супермаркеты"  # Должен быть вторым (2.0)


def test_top_categories_cashback_file_error():
    """Тестирует обработку ошибки чтения файла."""
    with patch("pandas.read_excel", side_effect=FileNotFoundError("File not found")):
        with pytest.raises(FileNotFoundError):
            top_categories_cashback("nonexistent.xlsx", 10, 2021)


def test_top_categories_cashback_json_format():
    """Тестирует корректность JSON-формата вывода."""
    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame(TEST_DATA)

        result = top_categories_cashback("dummy_path.xlsx", 10, 2021)

        # Проверяем, что результат - валидный JSON
        data = json.loads(result)
        assert isinstance(data, dict)

        # Проверяем содержание данных без учета форматирования
        expected_data = {
            "Рестораны": 2.0,
            "Супермаркеты": 1.5
        }
        assert data == expected_data
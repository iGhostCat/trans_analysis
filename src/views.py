import json
import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv("../.env")
API_KEY = os.getenv("API_KEY")


def excel_to_list_of_dicts(path_to_file):
    """Функция преобразования таблицы .xlsx в список словарей"""
    df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям", header=0)
    transactions = []
    for _, row in df.iterrows():
        transaction = {
            "Дата операции": row["Дата операции"],
            "Дата платежа": row["Дата платежа"],
            "Номер карты": row["Номер карты"],
            "Статус": row["Статус"],
            "Сумма операции": row["Сумма операции"],
            "Валюта операции": row["Валюта операции"],
            "Сумма платежа": row["Сумма платежа"],
            "Валюта платежа": row["Валюта платежа"],
            "Кэшбэк": row["Кэшбэк"],
            "Категория": row["Категория"],
            "MCC": row["MCC"],
            "Описание": row["Описание"],
            "Бонусы (включая кэшбэк)": row["Бонусы (включая кэшбэк)"],
            "Округление на инвесткопилку": row["Округление на инвесткопилку"],
            "Сумма операции с округлением": row["Сумма операции с округлением"],
        }
        transactions.append(transaction)

    return transactions


def excel_to_dataframe(path_to_file):
    '''Функция преобразования таблицы xlsx в датафрейм pandas'''
    df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям", header=0)
    return df


def transactions_to_json(transactions):
    """
    Преобразует список транзакций в JSON-строку.

    Args:
        transactions (list): Список словарей с транзакциями.

    Returns:
        str: JSON-строка с транзакциями.
    """

    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    return json.dumps(
        transactions,
        ensure_ascii=False,
        indent=4,
        default=default_serializer
    )


#trans_list = excel_to_list_of_dicts("../data/test_operations.xlsx")
#print(transactions_to_json(trans_list))


def sums_by_category(transactions_dataframe):
    status_filtered = transactions_dataframe[transactions_dataframe['Статус'] == 'OK']
    expenses_filtered = status_filtered[status_filtered['Сумма операции'] < 0]
    cards_groups = expenses_filtered.groupby('Номер карты')
    sum_by_category = cards_groups['Сумма операции с округлением'].sum()
    return sum_by_category

trans_df = excel_to_dataframe("../data/test_operations.xlsx")
print( sums_by_category(trans_df))

def top_transactions(transactions_df):
    sorted_df = transactions_df.sort_values(by='Сумма операции с округлением', ascending=False)
    top = []
    for col, row in sorted_df[0:4].iterrows():
        transaction = {
            "Дата операции": row["Дата операции"],
            "Дата платежа": row["Дата платежа"],
            "Номер карты": row["Номер карты"],
            "Статус": row["Статус"],
            "Сумма операции": row["Сумма операции"],
            "Валюта операции": row["Валюта операции"],
            "Сумма платежа": row["Сумма платежа"],
            "Валюта платежа": row["Валюта платежа"],
            "Кэшбэк": row["Кэшбэк"],
            "Категория": row["Категория"],
            "MCC": row["MCC"],
            "Описание": row["Описание"],
            "Бонусы (включая кэшбэк)": row["Бонусы (включая кэшбэк)"],
            "Округление на инвесткопилку": row["Округление на инвесткопилку"],
            "Сумма операции с округлением": row["Сумма операции с округлением"],
        }
        top.append(transaction)
    return top

print(top_transactions(trans_df))

def currency_rates_api(currencies = None):
    """
    Получает актуальные курсы валют к рублю из API ЦБ РФ

    Args:
        currencies (list): Список валют для получения (например ['USD', 'EUR'])
                           Если None, возвращает все доступные валюты

    Returns:
        list: Список словарей в формате [{"currency": "USD", "rate": 73.21}, ...]
    """
    try:
        # Делаем запрос к API ЦБ РФ
        response = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
        response.raise_for_status()  # Проверяем на ошибки
        data = response.json()

        # Получаем данные по валютам
        valutes = data['Valute']

        # Фильтруем валюты, если задан список
        if currencies is not None:
            valutes = {code: v for code, v in valutes.items() if code in currencies}

        # Формируем результат
        result = [
            {"currency": code, "rate": v['Value']}
            for code, v in valutes.items()
        ]

        return result

    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при получении курсов валют: {str(e)}")
print(currency_rates_api(['USD', 'EUR']))
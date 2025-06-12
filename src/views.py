import json
import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv("../.env")
API_KEY_EXCHANGE_RATES = os.getenv("API_KEY_EXCHANGE_RATES")
API_KEY_FIN_MODELING = os.getenv("API_KEY_FIN_MODELING")


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
    """Функция преобразования таблицы xlsx в датафрейм pandas"""
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

    return json.dumps(transactions, ensure_ascii=False, indent=4, default=default_serializer)


# trans_list = excel_to_list_of_dicts("../data/test_operations.xlsx")
# print(transactions_to_json(trans_list))


def sums_by_category(transactions_dataframe):
    """
    Возвращает сумму трат и кэшбэка по последним 4 цифрам карт в JSON-формате

    Args:
        transactions_dataframe: DataFrame с транзакциями

    Returns:
        dict: Данные в формате {"cards": [...]}
    """

    status_filtered = transactions_dataframe[transactions_dataframe["Статус"] == "OK"].copy()
    expenses_filtered = status_filtered[status_filtered["Сумма операции"] < 0].copy()

    expenses_filtered.loc[:, "last_digits"] = expenses_filtered["Номер карты"].str[-4:]

    cards_groups = (
        expenses_filtered.groupby("last_digits")
        .agg({"Сумма операции с округлением": "sum", "Кэшбэк": "sum"})
        .reset_index()
    )

    cards_groups["total_spent"] = cards_groups["Сумма операции с округлением"].abs()
    cards_groups["cashback"] = cards_groups["Кэшбэк"]

    # Форматирование результата
    result = {
        "cards": cards_groups[["last_digits", "total_spent", "cashback"]]
        .rename(columns={"last_digits": "last_digits"})
        .to_dict("records")
    }

    return result


# trans_df = excel_to_dataframe("../data/test_operations.xlsx")
# print(sums_by_category(trans_df))


def top_transactions(transactions_df):
    sorted_df = transactions_df.sort_values(by="Сумма операции с округлением", ascending=False)
    top = []
    for _, row in sorted_df.head(5).iterrows():
        transaction = {
            "date": row["Дата операции"],
            "amount": row["Сумма операции"],
            "category": row["Категория"],
            "description": row["Описание"],
        }
        top.append(transaction)
    return {"top_transactions": top}


# print(top_transactions(trans_df))


def currency_rates_api(currencies_file):
    """
    Получает актуальные курсы валют к рублю из API ЦБ РФ

    Args:
        currencies_file (str): Путь к JSON-файлу с валютами

    Returns:
        list: Список словарей в формате [{"currency": "USD", "rate": 73.21}, ...]
    """
    try:
        # 1. Загружаем список валют из файла
        with open(currencies_file, "r") as f:
            data = json.load(f)
            currencies = data.get("user_currencies", [])  # Обратите внимание на имя ключа

        # 2. Делаем запрос к API ЦБ РФ
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
        response.raise_for_status()
        api_data = response.json()

        # 3. Получаем данные по валютам
        valutes = api_data["Valute"]

        # 4. Фильтруем валюты по запрошенному списку
        if currencies:  # Если список валют не пустой
            valutes = {code: v for code, v in valutes.items() if code in currencies}

        # 5. Формируем результат
        result = [{"currency": code, "rate": round(v["Value"], 2)} for code, v in valutes.items()]

        return result

    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при получении курсов валют: {str(e)}")
    except (KeyError, json.JSONDecodeError) as e:
        raise Exception(f"Ошибка обработки данных: {str(e)}")


# print(currency_rates_api("../user_settings.json"))


def get_stock_prices(input_file, api_key):
    """
    Получает текущие цены акций из S&P500 по списку тикеров

    """
    # 1. Загружаем список тикеров из JSON-файла
    with open(input_file, "r") as f:
        data = json.load(f)
        tickers = data.get("user_stocks", [])

    # 2. Делаем запрос к API для каждого тикера
    stock_prices = []
    base_url = "https://financialmodelingprep.com/api/v3/quote-short/"

    for ticker in tickers:
        try:
            response = requests.get(f"{base_url}{ticker}?apikey={api_key}")
            response.raise_for_status()
            quote = response.json()[0]

            stock_prices.append({"stock": ticker, "price": quote["price"]})
        except (requests.RequestException, IndexError, KeyError) as e:
            print(f"Ошибка при получении данных для {ticker}: {str(e)}")
            continue

    # 3. Возвращаем результат в требуемом формате
    return {"stock_prices": stock_prices}


# print(get_stock_prices("../user_settings.json", API_KEY_FIN_MODELING))

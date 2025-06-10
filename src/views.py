import pandas as pd
import openpyxl
import json

def excel_to_list_of_dicts(path_to_file):
    """Функция преобразования таблицы .xlsx в список словарей"""
    df = pd.read_excel(
        path_to_file,
        sheet_name="Отчет по операциям",
        header=0
    )
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
            "Сумма операции с округлением": row["Сумма операции с округлением"]
        }
        transactions.append(transaction)

    return transactions

def list_of_dicts_to_json(transactions):
    return json.dump(transactions)
trans_list = excel_to_list_of_dicts("../data/test_operations.xlsx")
print(list_of_dicts_to_json(trans_list))

from datetime import datetime


def greetings():
    """Функция анализирует системное время на устройстве и выдаёт соответствующее приветствие"""
    date_time_now = datetime.now()
    current_time = date_time_now.time()
    greeting = ""
    if current_time.hour in range(4, 12):
        greeting = "Доброе утро!"
    elif current_time.hour in range(12, 16):
        greeting = "Добрый день!"
    elif current_time.hour in range(16, 24):
        greeting = "Добрый вечер!"
    elif current_time.hour in range(0, 4):
        greeting = "Доброй ночи!"
    return greeting


def main():
    print(greetings())


main()

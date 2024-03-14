import requests
import logging
import config
import sqlite3
import telebot
from database import execute_selection_query

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(message)s")


GPT_MODEL = 'yandexgpt'
# Ограничение на выход модели в токенах
MAX_MODEL_TOKENS = 50
# Креативность GPT (от 0 до 1)
MODEL_TEMPERATURE = 0.6

DB_DIR = 'db'
DB_NAME = 'db.sqlite'
DB_TABLE_USERS_NAME = 'users'

TOKEN = config.iam_token  # Токен для доступа к YandexGPT изменяется каждые 12 часов
FOLDER_ID = config.folder_id  # Folder_id для доступа к YandexGPT

# Подсчитывает количество токенов в сессии
# messages - все промты из указанной сессии
def count_tokens(messages: sqlite3.Row):
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
       "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
       "maxTokens": MAX_MODEL_TOKENS,
       "messages": []
    }

        # Проходимся по всем сообщениям и добавляем их в список
    for row in messages:
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["content"]
            }
        )


    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
            json=data,
            headers=headers
        ).json()["tokens"]
    )


# Функция получает идентификатор пользователя, чата и самого бота, чтобы иметь возможность отправлять сообщения
def is_tokens_limit(user_id, chat_id, tokens, bot):
    # В зависимости от полученного числа выводим сообщение
    if tokens >= MAX_MODEL_TOKENS:
        bot.send_message(
              chat_id,
              f'Вы израсходовали все токены в этой сессии. Вы можете начать новую, введя help_with')

    elif tokens + 50 >= MAX_MODEL_TOKENS:# Если осталось меньше 50 токенов
        bot.send_message(
            chat_id,
            f'Вы приближаетесь к лимиту в {MAX_MODEL_TOKENS} токенов в этой сессии. '
            f'Ваш запрос содержит суммарно {tokens} токенов.')

    elif tokens / 2 >= MAX_MODEL_TOKENS:# Если осталось меньше половины
        bot.send_message(
            chat_id,
            f'Вы использовали больше половины токенов в этой сессии. '
            f'Ваш запрос содержит суммарно {tokens} токенов.'
          )


# Выполняем запрос к YandexGPT
def ask_gpt(text, role):
    """Запрос к Yandex GPT"""

    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": MODEL_TEMPERATURE,
            "maxTokens": MAX_MODEL_TOKENS
        },
        "messages": [
            {"role": "system", "text": role}, #роль нейросети в диалоге
            {"role": "user", "text": text}, #задание от пользователя
            # Можно продолжить диалог
            {"role": "assistant", "text": ""}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logging.debug(f"Response {response.json()} Status code:{response.status_code} Message {response.text}")
            result = f"Status code {response.status_code}. Подробности см. в журнале."
            return result
        print("\n\nТУТ", response.json(), "ТУТ\n\n")
        result = response.json()['result']['alternatives'][0]['message']['text']
        logging.info(f"Request: {response.request.url}\n"
                     f"Response: {response.status_code}\n"
                     f"Response Body: {response.text}\n"
                     f"Processed Result: {result}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        result = "Произошла непредвиденная ошибка. Подробности см. в журнале."

    return result
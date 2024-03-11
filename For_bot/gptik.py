import logging
from for_SQL import SQL
import requests
import telebot
from telebot import types
import config
import nou
from transformers import AutoTokenizer
import GPT

bot = telebot.TeleBot(token=config.token)
answer = ''
user = {}
max_tokens_in_task = 2048
system_content = {}
task = {}
sql = SQL()
assistant_content = 'Ответь на вопрос:'

def count_tokens(text):
    tokenizer = AutoTokenizer.from_pretrained("rhysjones/phi-2-orange")  # название модели
    return len(tokenizer.encode(text))



@bot.message_handler(commands=['help'])
def help_function(message):
    user_id = message.chat.id
    bot.send_message(user_id, text='С помощью команд: \n'
                                   '/start - бот начнёт диалог заново'
                                   '/solve_task - можно задать роль боту \n'
                                   '/continue - бот продолжит формулировать ответ')

#обработка команды start
@bot.message_handler(commands=['start'])
def start_function(message):
    #создание таблицы и бд с помощью функций
    sql.create_db()
    sql.create_table()

    #имя пользователя сохраняется в переменных
    user_name = message.from_user.first_name

    keyboard = types.InlineKeyboardMarkup()
    but1 = types.InlineKeyboardButton(text='Начать!', callback_data='button_1')
    keyboard.add(but1)
    bot.send_message(message.chat.id, text=f"Приветствую тебя, {user_name}!", reply_markup=keyboard)

    user_id = message.from_user.id
    sql.insert_data(user_id=user_id)

    #переход к следующей функции
    bot.register_next_step_handler_by_chat_id(message, subject)



@bot.callback_query_handler(func=lambda call: call.data == 'button_1')
def subject(message):
    user_id = message.from_user.id
    keyboard = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton('Детектив')
    button_2 = types.KeyboardButton('Фэнтези')
    button_3 = types.KeyboardButton('Драма')
    keyboard.add(button_1, button_2)
    keyboard.add(button_3)
    bot.send_message(user_id, text="Выбери интересующий тебя жанр: ", reply_markup=keyboard)

    bot.register_next_step_handler_by_chat_id(message, level)



@bot.message_handler()
def level(message):
    user_id = message.from_user.id
    text = message.text

    if text == 'Детектив':
        sql.update_data(user_id, 'genre', 'Детектив')
    elif text == 'Фэнтези':
        sql.update_data(user_id, 'genre', 'Фэнтези')
    elif text == 'Драма':
        sql.update_data(user_id, 'genre', 'Драма')
    else:
        bot.send_message(user_id, text='Данные введены некорректно. Нажмите на кнопку клавиатуры.')
        bot.register_next_step_handler_by_chat_id(message, subject)

    global task
    task[user_id] = (f" Давай подробный ответ с решением на русском языке"
                          f"генерируй сценарий по жанру: {text}")

    keyboard = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton(text='Мелисса♀️')
    button_2 = types.KeyboardButton(text='Исидор♂️')
    button_3 = types.KeyboardButton(text='Мария♀️')
    button_4 = types.KeyboardButton(text='Эйзак♂️')
    keyboard.add(button_1, button_2)
    keyboard.add(button_3, button_4)

    bot.send_message(user_id, text='Выбери главного героя:', reply_markup=keyboard)

    bot.register_next_step_handler(message, solve_task)


@bot.message_handler()
def solve_task(message):
    user_id = message.from_user.id

    if message.text == 'Мелисса♀️':
        sql.update_data(user_id, 'character', 'Мелисса')
    elif message.text == 'Исидор♂️':
        sql.update_data(user_id, 'character', 'Исидор')
    elif message.text == 'Мария♀️️':
        sql.update_data(user_id, 'character', 'Мария')
    elif message.text == 'Эйзак♂️':
        sql.update_data(user_id, 'character', 'Эйзак')
    else:
        bot.send_message(user_id, text='Данные введены некорректно. Нажмите на кнопку клавиатуры.')
        bot.register_next_step_handler_by_chat_id(message, level)

    text = message.text
    global task
    task[user_id] += f"Главным героем, генерируемого сценария является: {text}"

    #создание клавиатуры
    keyboard = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton(text='Гарри Поттер')
    button_2 = types.KeyboardButton(text='Звёздные войны')
    button_3 = types.KeyboardButton(text='Marvel')
    keyboard.add(button_1)
    keyboard.add(button_2, button_3)

    bot.send_message(user_id, text="Выбери интересующий тебя фандом: ", reply_markup=keyboard)

    bot.register_next_step_handler(message, finals)

@bot.message_handler()
def finals(message):
    user_id = message.from_user.id

    if message.text == 'Гарри Поттер':
        sql.update_data(user_id, 'universal', 'Гарри Поттер')
    elif message.text == 'Звёздные войны':
        sql.update_data(user_id, 'universal', 'Звёздные войны')
    elif message.text == 'Marvel️':
        sql.update_data(user_id, 'universal', 'Marvel')
    else:
        bot.send_message(user_id, text='Данные введены некорректно. Нажмите на кнопку клавиатуры.')
        bot.register_next_step_handler_by_chat_id(message, level)

    text = message.text
    global task
    task[user_id] += f"Главным героем, генерируемого сценария является: {text}"

    sql.update_data(user_id, 'task', f'{task[user_id]}')
    sql.update_data(user_id, 'answer', '')

    keyboard = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton(text='Начать!')
    keyboard.add(button_1)

    bot.send_message(user_id, text="Нажми 'Начать' для генерации сценария!", reply_markup=keyboard)

    bot.register_next_step_handler(message, answer_function)



#Команда, присылающая ответ от нейросети
@bot.message_handler(commands=['answer'])
def answer_function(call):
    user_id = call.message_id
    result = sql.select_info(user_id)
    user_promt = result['task']
    answer = result['answer']

    try:
        results = GPT.ask_gpt(text=user_promt)

        #создание клавиатуры
        keyboard = types.InlineKeyboardMarkup()
        button_1 = types.InlineKeyboardButton(text='Закончить', callback_data='button1')
        button_2 = types.InlineKeyboardButton(text='Продолжить генерацию', callback_data='button2')
        keyboard.add(button_1, button_2)
        bot.send_message(call.message.chat.id, text=results, reply_markup=keyboard)

        if call.data != 'button2':
            #удаление ненужного
            sql.delete(user_id)

            task[user_id] = ''

            #возвращение к началу
            bot.register_next_step_handler(call, subject)
        else:
            task[user_id] += f'{results}'
            sql.update_data(user_id, 'task', f'{task[user_id]}')
            return
    except:

        bot.reply_to(
            call,
            f"Извини, я не смог сгенерировать для тебя ответ сейчас",
        )


bot.polling()

import logging
from database import(
    create_db,
    create_table,
    insert_data,
    add_record_to_table,
    execute_selection_query,
    is_limit_users
)
import requests
import telebot
from datetime import datetime
from telebot import types
import config
import nou
from transformers import AutoTokenizer
import GPT
import sqlite3


user = {}
session = {}
max_tokens_in_task = 2048
system_content = {}
task = {}
assistant_content = 'Ответь на вопрос:'
role = 'Ты сценарист и должен написать красивую историю. Пиши на русском языке'

max_session = 3
try:
    bot = telebot.TeleBot(token=config.token)
except:
    token = input(str('Напиши токен бота'))
    bot = telebot.TeleBot(token=token)

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
    create_db()
    create_table('users')

    limit = is_limit_users()

    if limit == True:
        bot.send_message(message.chat.id, text='Бот в данный момент не доступен')
        return

    #имя пользователя сохраняется в переменных
    user_name = message.from_user.first_name

    keyboard = types.InlineKeyboardMarkup()
    but1 = types.InlineKeyboardButton(text='Начать!', callback_data='button_1')
    keyboard.add(but1)
    bot.send_message(message.chat.id, text=f"Приветствую тебя, {user_name}! Я бот, создающий истории с помощью нейросети"
                                           f"Мы будем писать историю поочерёдно. Я начну, а ты должен продолжить \n"
                                           f"Нажми кнопку, чтобы начать,а когда захочешь выйти напиши /end",
                     reply_markup=keyboard)

    user_id = message.from_user.id
    insert_data(user_id=user_id)

    global user
    user[user_id] = {}

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

    global user
    user[user_id]['genre'] = f"{text}"

    keyboard = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton(text='Гермиона♀️')
    button_2 = types.KeyboardButton(text='Исидор♂️')
    button_3 = types.KeyboardButton(text='Дори♀️')
    button_4 = types.KeyboardButton(text='Гендальф♂️')
    keyboard.add(button_1, button_2)
    keyboard.add(button_3, button_4)

    bot.send_message(user_id, text='Выбери главного героя:', reply_markup=keyboard)

    bot.register_next_step_handler(message, solve_task)


@bot.message_handler()
def solve_task(message):
    user_id = message.from_user.id
    text = message.text

    global user
    user[user_id]['character'] = f"{text}"

    #создание клавиатуры
    keyboard = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton(text='Путешествие')
    button_2 = types.KeyboardButton(text='Битва')
    button_3 = types.KeyboardButton(text='Магия')
    keyboard.add(button_1)
    keyboard.add(button_2, button_3)

    bot.send_message(user_id, text="Выбери интересующий тебя фандом: ", reply_markup=keyboard)

    bot.register_next_step_handler(message, finals)

@bot.message_handler()
def finals(message):
    user_id = message.from_user.id

    text = message.text
    global user
    user[user_id]['setting'] += f"{text}"

    keyboard = types.ReplyKeyboardMarkup()
    button_1 = types.KeyboardButton(text='Начать!')
    keyboard.add(button_1)

    bot.send_message(user_id, text="Если ты хочешь ещё что-то добавить к истории, то напиши сейчас."
                                   "Или ты можешь нажать /begin для начала генерации", reply_markup=keyboard)

    session[user_id] += 1
    nou.max_session(user_id, user_id, session, bot)

    bot.register_next_step_handler(message, addition_function)

@bot.message_handler()
def addition_function(message):
    user_id = message.from_user.id
    text = message.text

    global user
    task[user_id]['additional_info'] = text

    bot.send_message(user_id, text='Спасибо! Мы учтём это при генерации текста. А теперь нажми /begin и я начну писать')

#Команда, присылающая ответ от нейросети
@bot.message_handler(commands=['begin'])
def answer_function(call):
    user_id = call.message_id
    user_answer = GPT.create_prompt(user, user_id)

    tokens: int = GPT.count_tokens(user_answer)

    if GPT.is_tokens_limit(user_id, user_id, tokens, bot):
        return

    row: sqlite3.Row = session[user_id]

    # создание новой строчки в таблице с user
    add_record_to_table(
        user_id,
        'user',
        user_answer,
        datetime.now(),
        tokens,
        row['session_id']
    )

    bot.send_message(user_id, 'Генерирую ответ...')
    try:

        results = GPT.ask_gpt(text=user_answer, role=role, mode='continue')

        tokens: int = count_tokens(results)

        if GPT.is_tokens_limit(user_id, user_id, tokens, bot):
            return

        #создание новой строчки в таблице с assistant
        add_record_to_table(
            user_id,
            'assistant',
            results,
            datetime.now(),
            tokens,
            row['session_id']
        )

        #создание клавиатуры
        keyboard = types.InlineKeyboardMarkup()
        button_1 = types.InlineKeyboardButton(text='Закончить', callback_data='button1')
        button_2 = types.InlineKeyboardButton(text='Продолжить генерацию', callback_data='button2')
        keyboard.add(button_1, button_2)
        bot.send_message(call.message.chat.id, text=results, reply_markup=keyboard)

        if call.data != 'button2':
            GPT.ask_gpt(text=user_answer, role=role, mode='end')
            #удаление ненужного
            task[user_id] = ''

            #возвращение к началу
            bot.register_next_step_handler(call, subject)
        else:
            task[user_id] += f'{results}'

            return
    except:

        bot.reply_to(
            call,
            f"Извини, я не смог сгенерировать для тебя ответ сейчас",
        )


bot.polling()

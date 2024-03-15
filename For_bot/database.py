import sqlite3
import logging


DB_DIR = 'db'
DB_NAME = 'db.sqlite'
DB_TABLE_USERS_NAME = 'users'
MAX_USERS = 3

    #создание базы данных
# Функция для подключения к базе данных или создания новой, если её ещё нет
def create_db(database_name=DB_NAME):
    db_path = f'{database_name}'
    connection = sqlite3.connect(db_path)
    connection.close()


# Функция для выполнения любого sql-запроса для изменения данных
def execute_query(db_file, query, data=None):
    """
    Функция для выполнения запроса к базе данных.
    Принимает имя файла базы данных, SQL-запрос и опциональные данные для вставки.
    """

    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    if data:
        cursor.execute(query, data)
    else:
        cursor.execute(query)

    connection.commit()
    connection.close()


# Функция для выполнения любого sql-запроса для получения данных (возвращает значение)
def execute_selection_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    try:
        logging.info(f"DATABASE: Execute query: {sql_query}")

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        if data:
            cursor.execute(sql_query, data)
        else:
            cursor.execute(sql_query)

        rows = cursor.fetchall()
        connection.close()
        return rows

    except sqlite3.Error as e:
        logging.error(f"DATABASE: Ошибка при запросе: {e}")
        print("Ошибка при выполнении запроса:", e)


#функция для создания любой таблицы
def create_table(table_name):
    sql_query = f'CREATE TABLE IF NOT EXISTS {table_name} ' \
                    f'(id INTEGER PRIMARY KEY, ' \
                    f'user_id INTEGER, ' \
                    f'role TEXT, ' \
                    f'content TEXT, ' \
                    f'date DATETIME, ' \
                    f'tokens TEXT, '\
                    f'session_id INTEGER)'
    execute_query(DB_NAME, sql_query)

def insert_data(self, user_id):
    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()

    query = '''INSERT INTO users (user_id) VALUES (?)'''
    cur.execute(query, (user_id, ))
    con.commit()
    con.close()


    #запрос к SQL по критериям
def update_data(self, user_id, column, value):
    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()

    #column - название поля в таблице users
    query = f'UPDATE users SET {column} = ? WHERE user_id = ?'
    cur.execute(query, (user_id, value, ))
    con.commit()
    con.close()

#извлечение информации о пользователе
def select_info(self, user_id):
    con = sqlite3.connect('db.sqlite')
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    query = f'SELECT * FROM users WHERE user_id = ?'
    cur.execute(query, (user_id, ))
    con.close()

#удаление данных пользователя с таблицы
def delete(self, user_id):
    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()

    query = f'DELETE * FROM users WHERE user_id = ?'
    cur.execute(query, (user_id,))
    con.commit()
    con.close()

#удаляет все записи из таблицу, надо записывать название таблицы
def delete_table(self, table_name):
    execute_query(f'DELETE FROM {table_name}')

 #функция для вставки новой строки в таблицу
def insert_row(table_name, values, columns=''):
    if columns != '':
        columns = '(' + ', '.join(columns) + ')'
    sql_query = f'INSERT INTO {table_name} {columns}VALUES ({", ".join(["?"] * len(values))})'
    execute_query(sql_query, values)

#добавление новой записи в таблицу
def add_record_to_table(user_id, role, content, date, tokens, session_id):
    insert_row(DB_TABLE_USERS_NAME,
               [user_id, role, content, date, tokens, session_id],
               columns=['user_id', 'role', 'content', 'date', 'tokens', 'session_id'])

def is_limit_users():
    connection = sqlite3.connect('sqlite3.db')

    cursor = connection.cursor()
    result = cursor.execute('SELECT DISTINCT user_id FROM table_name;')


    count = 0  # количество пользователей
    for i in result:  # считаем количество полученных строк
        count += 1  # одна строка == один пользователь
    connection.close()
    return count >= MAX_USERS
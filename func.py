import datetime

from configparser import ConfigParser
import psycopg2

def bot_token():

    config = ConfigParser()
    config.read('config.ini')
    token = config['bot']['token']
    return token


def config(filename='config.ini', section='database'):
    # Создаем парсер для файла конфигурации
    parser = ConfigParser()
    # Читаем конфигурационный файл
    parser.read(filename)

    # Получаем секцию конфигурации
    db_params = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_params[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')

    return db_params

def connect():
    conn = None
    try:
        # Чтение параметров подключения из конфигурационного файла
        params = config()

        print('Connecting to the PostgreSQL database...')
        # Подключение к PostgreSQL
        conn = psycopg2.connect(**params)

        # Возвращаем соединение
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

def select_actual_lessons():
    conn = None
    cur = None
    try:
        # Подключаемся к базе данных
        conn = connect()
        # Создаем курсор для выполнения SQL-запросов
        cur = conn.cursor()

        # Выполняем SQL-запрос для выбора всех значений из таблицы lessons_table
        cur.execute("SELECT DISTINCT ht.lessons , lt.lessons_name, lt.ico "
                    "FROM homework_table ht JOIN lessons_table lt ON ht.lessons = lt.id_lessons "
                    "WHERE ht.date_off >= CURRENT_DATE;")

        # Получаем все строки результата
        rows = cur.fetchall()
        # print(rows)
        # # Выводим результат на экран
        # for row in rows:
        #     print(row)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        # Закрываем курсор и соединение
        if cur:
            cur.close()
        if conn:
            conn.close()
            print('Database connection closed.')
        return rows


def get_homework_for_today_or_later(lesson_id):
    conn = None
    cur = None
    try:
        # Подключаемся к базе данных
        conn = connect()
        # Создаем курсор для выполнения SQL-запросов
        cur = conn.cursor()

        # Получаем текущую дату
        today = datetime.date.today()

        # Выполняем SQL-запрос для выбора данных из таблицы homework_table
        cur.execute("""
            SELECT ht.*, lt.lessons_name
            FROM homework_table ht
            JOIN lessons_table lt ON ht.lessons = lt.id_lessons
            WHERE ht.lessons = %s AND ht.date_off >= %s
        """, (lesson_id, today))

        # Получаем все строки результата
        rows = cur.fetchall()

        # Создаем список для хранения результатов
        results = []
        print(rows)

        # Добавляем результаты в список
        for row in rows:
            # Преобразуем даты в более удобочитаемый формат
            date_on = row[1].strftime('%Y-%m-%d')
            date_off = row[2].strftime('%Y-%m-%d')
            results.append({
                "date_on": date_on,
                "date_off": date_off,
                "lesson": row[6],
                "homework": row[4],
                "author": row[5]
            })

        return results
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None
    finally:
        # Закрываем курсор и соединение
        if cur:
            cur.close()
        if conn:
            conn.close()
            print('Database connection closed.')


def generate_homework_message(homework_results):

    lesson = homework_results[0]['lesson']  # Получаем название предмета
    # Получение текущей даты
    current_date = datetime.datetime.now()

    if not homework_results:
        return f"**{lesson}**\nНа сегодняшний день нет домашних заданий."

    # Сортируем задания по дате сдачи
    sorted_homework = sorted(homework_results, key=lambda x: x['date_off'])

    message = f"<b><u>{lesson}</u></b>\nДомашнее задание по предмету:\n\n"

    for idx, result in enumerate(sorted_homework, start=1):
        date_on = result['date_on']
        date_off = result['date_off']
        homework = result['homework']
        author = result['author']
        # Преобразование строки в объект datetime
        specified_date = datetime.datetime.strptime(date_off, "%Y-%m-%d")
        # Вычисление разницы в днях
        difference_in_days = (current_date - specified_date).days

        message += f"{idx}. <b><u>{homework}</u></b>.\n"
        message += f"   - <b><u>Срок сдачи</u></b> {date_off}.\n"
        message += f"   - <b><u>Осталось дней:</u></b> {abs(difference_in_days)}.\n"
        message += f"   - Добавлено: {author} {date_on}\n\n"

    return message
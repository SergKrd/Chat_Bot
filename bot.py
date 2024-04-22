from func import (
    bot_token,
    select_actual_lessons,
    get_homework_for_today_or_later, generate_homework_message,

)
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

temp_files_info_dict = {}
temp_folder_info_dict = {}
temp_folder_filtered_files_dict = {}

# Определение состояний
FIRST, HOMEWORK, BLANKS, BLANKS_FILE_CHOICE, LOCATION, JOKES, OTHER = range(7)  # Состояния


def find_files():
    """
    Функция для получения информации о файлах в указанной директории и её подпапках.
    Полученные данные сохраняются в переменную temp_blanks_data.
    """
    global temp_files_info_dict, temp_folder_info_dict

    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs_for_bot")
    files_info_dict = {}
    folder_info_dict = {}
    file_number = 1  # Переменная для сквозной нумерации файлов

    # Проходимся по каждой подпапке в указанной директории
    for root, dirs, files in os.walk(directory):
        for directory_name in dirs:
            # Получаем название папки
            folder_name = directory_name

            # Получаем полный путь к папке
            folder_path = os.path.join(root, directory_name)

            # Получаем список файлов внутри папки
            folder_files = os.listdir(folder_path)

            # Формируем список кортежей (название папки, название файла, полный путь) для данной папки
            for file_name in folder_files:
                file_path = os.path.join(folder_path, file_name)
                files_info_dict[file_number] = (folder_name, file_name, file_path)
                file_number += 1  # Увеличиваем номер для следующего файла

            # Формируем кортеж (номер, название файла, полный путь) для последнего добавленного файла
            # и добавляем его в словарь folder_info_dict
            if folder_files:
                last_file_name = folder_files[-1]
                last_file_path = os.path.join(folder_path, last_file_name)
                folder_info_dict[folder_name] = (
                    str(file_number - len(folder_files) + 1), last_file_name, last_file_path)

    temp_files_info_dict = files_info_dict
    temp_folder_info_dict = folder_info_dict
    return files_info_dict, folder_info_dict


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).

    keyboard = [[InlineKeyboardButton("Домашнее задание", callback_data='homework'),
                 InlineKeyboardButton("Бланки", callback_data='blanks')],
                [InlineKeyboardButton("Местоположение", callback_data='location'),
                 InlineKeyboardButton("Анекдоты", callback_data='jokes')],
                [InlineKeyboardButton("Другое", callback_data='other')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.message.reply_text("Выбери, что ты хочешь сделать", reply_markup=reply_markup, parse_mode='HTML')
    # Tell ConversationHandler that we're in state `FIRST` now
    return FIRST


async def first_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global temp_folder_info_dict, temp_files_info_dict
    user_choice = update.callback_query.data
    query = update.callback_query
    print(user_choice)



    if user_choice == 'homework':
        # Обрабатываем выбор "Домашка"
        buttons = [[InlineKeyboardButton(f'{el[2]}   {el[1]}', callback_data=el[0])] for el in select_actual_lessons()]
        print(buttons)

        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text('Выберите предмет из списка:', reply_markup=reply_markup)
        return HOMEWORK
    elif user_choice == 'blanks':
        # Обрабатываем выбор "Бланки". Пользователю предлагается выбрать категорию документа
        find_files()
        # Получаем уникальные значения категорий
        files_category = set(
            item[0] for item in temp_files_info_dict.values())
        # Формируем кнопки для отправки в InlineKeyboard
        buttons = [[InlineKeyboardButton(category, callback_data=category)] for category in files_category]
        await query.edit_message_text('Выберите категорию бланков:', reply_markup=InlineKeyboardMarkup(buttons))
        return BLANKS
    elif user_choice == 'location':
        # Обрабатываем выбор "Местоположение"
        # Здесь можно реализовать логику для запроса местоположения пользователя
        await query.edit_message_text('Пожалуйста, отправьте свое местоположение:')
        return LOCATION
    elif user_choice == 'jokes':
        # Обрабатываем выбор "Анекдоты"
        # Здесь можно реализовать логику для отправки анекдотов пользователю
        await query.edit_message_text('Здесь будут анекдоты!')
        return ConversationHandler.END
    elif user_choice == 'other':
        # Обрабатываем выбор "Другое"
        await query.edit_message_text('Вы выбрали "Другое".')
        return ConversationHandler.END


async def homework_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Обработка выбора предмета для домашки
    user_choice = update.callback_query.data
    query = update.callback_query
    print(user_choice)
    print(query)
    if user_choice == 'back':
        return start(update, context)
    # Здесь можно вызвать функцию для получения информации о домашке по выбранному предмету
    # и отправить ее пользователю
    homework_results = get_homework_for_today_or_later(user_choice)
    # Формируем сообщение с информацией о домашних заданиях
    homework_message = generate_homework_message(homework_results)
    await query.edit_message_text(homework_message, parse_mode='HTML')
    return ConversationHandler.END


async def blanks_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Выбор файла для отправки пользователю
    """
    # Обработка выбора бланков
    global temp_files_info_dict, temp_folder_info_dict, temp_folder_filtered_files_dict
    user_choice = update.callback_query.data
    query = update.callback_query
    print('blanks_choice', user_choice)
    if user_choice == 'back':
        return start(update, context)
    # Здесь можно вывести список файлов и позволить пользователю выбрать один из них
    filtered_data = {key: value for key, value in temp_files_info_dict.items() if value[0] == user_choice}
    temp_folder_filtered_files_dict = filtered_data

    # Получаем имена файлов из словаря
    selected_files = [(key, value[1]) for key, value in temp_folder_filtered_files_dict.items()]

    print('selected_files', selected_files)
    # Добавляем кнопки для каждого файла
    buttons = [[InlineKeyboardButton(file[1], callback_data=file[0])] for file in selected_files]
    await query.edit_message_text('Выберите нужный документ:', reply_markup=InlineKeyboardMarkup(buttons))
    return BLANKS_FILE_CHOICE


async def blanks_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправка выбранного файла пользователю
    """
    # Обработка выбора бланков
    global temp_files_info_dict, temp_folder_info_dict, temp_folder_filtered_files_dict
    user_choice = update.callback_query.data
    query = update.callback_query
    if user_choice == 'back':
        return start(update, context)
    # Отправляем файл пользователю
    file_path = temp_folder_filtered_files_dict[int(user_choice)][2]# Путь к файлу на диске
    file_name = f'"{temp_folder_filtered_files_dict[int(user_choice)][1]}"'  # Имя файла

    await query.edit_message_text(
        f'Отправляю документ {file_name} пользователю "{query.from_user.first_name}"'
    )

    try:
        with open(file_path, 'rb') as file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=file,
                filename=file_name,
                caption=f"Документ: {file_name}"
            )
    except FileNotFoundError:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"Ошибка: файл '{file_path}' не найден."
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Заходи если чё...!")
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token()).build()

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [CallbackQueryHandler(first_choice)],
            HOMEWORK: [CallbackQueryHandler(homework_choice)],
            BLANKS: [CallbackQueryHandler(blanks_choice)],
            BLANKS_FILE_CHOICE: [CallbackQueryHandler(blanks_send)],
            LOCATION: [CallbackQueryHandler(cancel)],
            JOKES: [CallbackQueryHandler(cancel)],
            OTHER: [CallbackQueryHandler(cancel)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

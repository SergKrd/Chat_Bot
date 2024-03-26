import telebot
import configparser

# Создание объекта ConfigParser
config = configparser.ConfigParser()
# Чтение файла конфигурации
config.read('config.ini')
# Получение значений из конфигурационного файла
BotToken = config['bot']['TOKEN']

bot = telebot.TeleBot(BotToken)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 'Привет, это бот, который поможет вам разобраться в вашей проблеме')


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.infinity_polling()

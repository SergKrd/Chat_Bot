import telebot
from environs import Env

bot = telebot.TeleBot("token")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 'Привет, это бот, который поможет вам разобраться в вашей проблеме')


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)



bot.infinity_polling()

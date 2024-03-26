import telebot

bot = telebot.TeleBot("7170034100:AAGWuoTvMLck5xTCApr6ysh_ILQ1rwD7kkM")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 'Привет, это бот, который поможет вам разобраться в вашей проблеме')


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)



bot.infinity_polling()

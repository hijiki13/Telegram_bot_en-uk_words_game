import telebot
import requests
import os
from telebot import types
# from secret import TOKEN
from deep_translator import GoogleTranslator

# please put in your own token
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
used_words = set()
last_l_u = ''
cur_word = ''
with open('corncob_lowercase.txt', 'r') as f:
    words = set()
    data = f.read().split('\n')
    for el in data:
        words.add(el)


@bot.message_handler(commands=['start'])
def welcome(msg):
    global used_words, last_l_u, cur_word
    last_l_u = ''
    cur_word = ''
    used_words = set()
    bot.send_message(msg.chat.id, "Let's start! Your word: ")


@bot.message_handler(content_types=['text'])
def game(msg):
    global last_l_u, cur_word

    if last_l_u:
        if invalid_word(msg, last_l_u):
            return

    if invalid_word(msg):
        return

    used_words.add(msg.text)
    words.remove(msg.text.lower())
    last_l = msg.text[-1].lower()

    for elem in words:
        if elem.startswith(last_l):
            cur_word = elem
            bot.send_message(msg.chat.id, f'Word starting with {last_l.upper()}: {elem.capitalize()} ', reply_markup=create_btns())
            used_words.add(elem)
            words.remove(elem)
            last_l_u = elem[-1]
            break
    else:
        bot.send_message(msg.chat.id, f'You win! Amazing job, congratulations! Words used in session: {len(used_words)}')
        return


def invalid_word(msg, last_l=None):
    msg_text = msg.text.lower()
    if last_l:
        if not msg_text.startswith(last_l):
            bot.send_message(msg.chat.id, f'Invalid word. Should start with {last_l.capitalize()}.')
            return True

    if msg_text in used_words:
        bot.send_message(msg.chat.id, 'This word was already used!')
        return True

    if msg_text not in words:
        bot.send_message(msg.chat.id, "Sorry, this is unknown word! Are you sure it's not a typo?")
        return True


def create_btns():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='Translate📝', callback_data='ts')
    btn2 = types.InlineKeyboardButton(text='Give Up🚫', callback_data='lost')
    markup.add(btn1, btn2)
    return markup


@bot.callback_query_handler(lambda query: query.data == 'ts')
def translate_word(query):
    bot.send_message(query.message.chat.id, f'Переклад: {cur_word.capitalize()} - {GoogleTranslator(target="uk", source="en").translate(cur_word).capitalize()}', reply_markup=def_btn())


def def_btn():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text='Показати визначення', callback_data='def')
    markup.add(btn)
    return markup


@bot.callback_query_handler(lambda query: query.data == 'def')
def show_def(query):
    req = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{cur_word}")
    definition = req.json()[0]['meanings'][0]['definitions'][0]['definition']
    bot.send_message(query.message.chat.id, f'Значення: {GoogleTranslator(target="uk", source="en").translate(definition).capitalize()}')


@bot.callback_query_handler(lambda query: query.data == 'lost')
def end_game(query):
    global used_words
    bot.send_message(query.message.chat.id, f'Game over! Words used in this session: {len(used_words)}. Good job!')
    used_words = set()
    return


bot.infinity_polling()

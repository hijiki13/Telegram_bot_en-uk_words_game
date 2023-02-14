import telebot
from telebot import types
import requests
import sqlalchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from os import getenv
# from secret import TOKEN
from deep_translator import GoogleTranslator


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    last_l_u: Mapped[str]
    cur_word: Mapped[str]
    used_words: Mapped[str]
    words: Mapped[str]
    

# please put in your own token
TOKEN = getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)


engine = sqlalchemy.create_engine("sqlite:///users.db")
connection = engine.connect()
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)


@bot.message_handler(commands=['start'])
def welcome(msg):
    session = Session(engine)

    with open('corncob_lowercase.txt', 'r') as f:
        words = f.read()

    with session as db:
        user = db.query(User).filter(msg.chat.id == User.user_id).first()
        
        if not user:
            user = User(
                user_id=msg.chat.id,
                last_l_u='',
                cur_word='',
                used_words='',
                words=words
            )
            db.add(user)
            db.commit()
        else:
            user.last_l_u = ''
            user.last_l = ''
            user.cur_word = ''
            user.used_words = ''
            user.words = words
            db.commit()

    bot.send_message(msg.chat.id, "Let's start! Your word: ")


@bot.message_handler(content_types=['text'])
def game(msg):
    session = Session(engine)

    if invalid_word(msg):
        return

    with session as db:
        user = session.query(User).filter(msg.chat.id == User.user_id).first()
        words = set(user.words.split('\n'))

        if user.last_l_u:
            if invalid_word(msg, user.last_l_u):
                return
            
        user.used_words += msg.text + '\n'
        words.remove(msg.text.lower())
        user.last_l = msg.text[-1].lower()
        db.commit()

        for elem in words:

            if elem.startswith(user.last_l):
                user.cur_word = elem
                bot.send_message(msg.chat.id, f'Word starting with {user.last_l.upper()}: {elem.capitalize()} ', reply_markup=create_btns())
                user.used_words += elem + '\n'
                words.remove(elem)
                user.words = '\n'.join(words)
                user.last_l_u = elem[-1]
                db.commit()
                break
        else:
            used_words = user.used_words.split('\n')
            bot.send_message(msg.chat.id, f'You win! Amazing job, congratulations! Words used in session: {len(used_words)-1}')
            return


def invalid_word(msg, last_l=None):
    session = Session(engine)
    msg_text = msg.text.lower()

    if last_l:
        if not msg_text.startswith(last_l):
            bot.send_message(msg.chat.id, f'Invalid word. Should start with {last_l.capitalize()}.')
            return True

    with session as db:
        user = db.query(User).filter(msg.chat.id == User.user_id).first()
        used_words = set(user.used_words.split('\n'))
        words = set(user.words.split('\n'))

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
    session = Session(engine)
    with session:
        cur_word = session.query(User).filter(query.message.chat.id == User.user_id).one().cur_word

    bot.send_message(query.message.chat.id, f'Переклад: {cur_word.capitalize()} - {GoogleTranslator(target="uk", source="en").translate(cur_word).capitalize()}', reply_markup=def_btn())


def def_btn():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text='Показати визначення', callback_data='def')
    markup.add(btn)
    return markup


@bot.callback_query_handler(lambda query: query.data == 'def')
def show_def(query):
    session = Session(engine)
    with session:
        cur_word = session.query(User).filter(query.message.chat.id == User.user_id).one().cur_word

    req = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{cur_word}")
    definition = req.json()[0]['meanings'][0]['definitions'][0]['definition']
    bot.send_message(query.message.chat.id, f'Визначення: {GoogleTranslator(target="uk", source="en").translate(definition).capitalize()}')


@bot.callback_query_handler(lambda query: query.data == 'lost')
def end_game(query):
    session = Session(engine)
    with session:
        used_words = session.query(User).filter(query.message.chat.id == User.user_id).one().used_words
        used_words = set(used_words.split('\n'))
    
    bot.send_message(query.message.chat.id, f'Game over! \nWords used in this session: {len(used_words)-1}. Good job!\n Please press /start to play again.')
    return


bot.infinity_polling()

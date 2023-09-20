import json
import sqlite3
import random
import telebot
from telebot import *

with open("Bot_Data.json") as data:
    bot_data = json.loads(data.read())

bot_token = bot_data["token"]
bot = telebot.TeleBot(bot_token, parse_mode = None)
bot_name = bot.get_me().username

cancel = ["cancel", "/cancel", f"/cancel@{bot_name.lower()}", "отмена"]

print("Бот включен!")


def sql(execute_command : str, command_parameters = None):
    base = sqlite3.connect("Bot_Data_Base.db")
    cursor = base.cursor()
    try:
        if command_parameters == None:
            cursor.execute(execute_command)
        else:
            cursor.execute(execute_command, command_parameters)
        result = cursor.fetchall()
    except:
        result = "ERROR"
    if len(result) == 0 or result[0][0] == "":
        result = None
    base.commit()
    base.close()
    return result

sql("CREATE TABLE IF NOT EXISTS users (id INTEGER UNIQUE, name TEXT, access INTEGER, distribution BOOLEAN)")
sql("CREATE TABLE IF NOT EXISTS birthdays (name TEXT UNIQUE, day INTEGER, month INTEGER, last_celebrated_year INTEGER)")

sql("CREATE TABLE IF NOT EXISTS days (day TEXT UNIQUE, is_work_day BOOLEAN)")
sql("CREATE TABLE IF NOT EXISTS rings (start_hour INTEGER, start_minute INTEGER, end_hour INTEGER, end_minute INTEGER, empty_lesson TEXT UNIQUE)")
sql("CREATE TABLE IF NOT EXISTS lessons (name TEXT UNIQUE, link TEXT, class TEXT, remind TEXT)")
sql("CREATE TABLE IF NOT EXISTS timetable (lesson_id INTEGER, flasher_id INTEGER)")

sql("CREATE TABLE IF NOT EXISTS stickers (id TEXT, unique_id TEXT UNIQUE, type TEXT)")

sticker_types = ["study", "happy", "lovely", "sad", "error", "service", "secret"]
def get_sticker(types : list = ["study", "happy", "lovely", "sad", "error", "service", "secret"]):
    try:
        type_ids = sql("SELECT id FROM stickers WHERE type = {}".format(f"\"{random.choice(types)}\""))
        print(random.choice(type_ids)[0])
        return random.choice(type_ids)[0]
    except:
        type_ids = sql("SELECT id FROM stickers WHERE type = {}".format(f"\"sad\""))
        print(random.choice(type_ids)[0])
        return random.choice(type_ids)[0]

def get_stickers_of_type(message):
    if message.text.lower() not in cancel:
        sticker_type = message.text[0 : message.text.index(' ')]
        if sticker_type in sticker_types:
            stickers_of_type = sql("SELECT id FROM stickers WHERE type = {}".format(f"\"{sticker_type}\""))
            if len(stickers_of_type) > 0:
                bot.send_message(message.chat.id, f"Стикеры типа {sticker_type}:", reply_markup = types.ReplyKeyboardRemove())
                for sticker_id in stickers_of_type:
                    bot.send_sticker(message.chat.id, sticker_id[0])
            else:
                bot.send_message(message.chat.id, "Стикеров этого типа нет.", reply_markup = types.ReplyKeyboardRemove())
        else:
            bot.send_message(message.chat.id, "Пожалуйста, выбирайте заготовленные ответы, а не пишите вручную. \n(＃￣ω￣) ",
                             reply_markup=types.ReplyKeyboardRemove())
    elif message.text.lower() in cancel:
        bot.send_message(message.chat.id, "Никаких действий со стикерами. \n(＃￣ω￣) ", reply_markup=types.ReplyKeyboardRemove())


editor = None
def sticker_action(message):
    if message.text.lower() not in cancel:
        if "режим редактора" in message.text:
            global editor
            if editor == None:
                editor = message.from_user.id
                bot.send_message(message.chat.id, "Для вас включен режим редактора. \n(＠＾◡＾)  ", reply_markup = types.ReplyKeyboardRemove())
            else:
                if editor == message.from_user.id:
                    editor = None
                    bot.send_message(message.chat.id, "Режим редактора выключен. \n(´• ω •`)  ", reply_markup = types.ReplyKeyboardRemove())
                else:
                    bot.send_message(message.chat.id, "Режим редактора включен другим пользователем. \n(♡μ_μ)  ",
                                     reply_markup = types.ReplyKeyboardRemove())
        elif "Получить стикеры типа..." == message.text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for sticker_type in sticker_types:
                stickers_of_type = sql("SELECT * FROM stickers WHERE type = {}".format(f"\"{sticker_type}\""))
                if stickers_of_type != None:
                    markup.add(types.KeyboardButton(f"{sticker_type} (кол-во: {len(stickers_of_type)})"))
            markup.add(types.KeyboardButton("Отмена"))
            ask_sticker_type = bot.send_message(message.chat.id, "Выберете тип стикеров:", reply_markup = markup)
            bot.register_next_step_handler(ask_sticker_type, get_stickers_of_type)
        elif "Удалить все стикеры" == message.text:
            if editor == None or editor == message.from_user.id:
                if sql("DELETE FROM stickers") != "ERROR":
                    bot.send_message(message.chat.id, "Все стикеры удалены. \n( _ _ )  ",
                                     reply_markup = types.ReplyKeyboardRemove())
                else:
                    bot.send_message(message.chat.id, "Ошибка удаления стикеров, проверьте базу данных. \n(♡μ_μ)  ",
                                     reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, "Сейчас стикеры редактируются, не будем нарушать процесс. \n(o˘◡˘o)  ",
                                 reply_markup = types.ReplyKeyboardRemove())
    elif message.text.lower() in cancel:
        bot.send_message(message.chat.id, "Никаких действий со стикерами. \n(＃￣ω￣) ", reply_markup = types.ReplyKeyboardRemove())


@bot.message_handler(commands = ["stickers"])
def stickers_msg(message):
    stickers = sql("SELECT * FROM stickers")
    if stickers == None:
        stickers = []

    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
    if editor == None:
        markup.add(types.KeyboardButton("Включить режим редактора"))
    else:
        markup.add(types.KeyboardButton("Выключить режим редактора"))
    markup.add(types.KeyboardButton("Получить стикеры типа..."))
    markup.add(types.KeyboardButton("Удалить все стикеры"))
    markup.add(types.KeyboardButton("Отмена"))

    ask_sticker_action = bot.send_message(message.chat.id, f"На данный момент в базе данных бота {len(stickers)} стикеров.", reply_markup = markup)
    bot.register_next_step_handler(ask_sticker_action, sticker_action)



@bot.message_handler(content_types = "sticker")
def sticker_msg(message):
    if str(message.chat.id)[0] != "-":

        if editor == message.from_user.id:
            class new_sticker:
                id = message.sticker.file_id
                unique_id = message.sticker.file_unique_id

            def delete_sticker(message):
                if message.text.lower() == "удалить":
                    sql("DELETE FROM stickers WHERE unique_id = {}".format(f"\"{new_sticker.unique_id}\""))
                    bot.send_message(message.chat.id, "Стикер успешно удалён!", reply_markup = types.ReplyKeyboardRemove())
                elif message.text.lower() == "отмена":
                    bot.send_message(message.chat.id, "Ничего со стикером не делаю.", reply_markup = types.ReplyKeyboardRemove())
                else:
                    bot.send_message(message.chat.id, "Ничего со стикером не делаю, неизвестная команда.", reply_markup = types.ReplyKeyboardRemove())

            def add_sticker(message):
                if message.text.lower() in sticker_types:
                    print(sql("INSERT INTO stickers VALUES ({}, {}, {})".format(f"\"{new_sticker.id}\"", f"\"{new_sticker.unique_id}\"", f"\"{message.text.lower()}\"")))
                    bot.send_message(message.chat.id, "Стикер успешно добавлен!", reply_markup = types.ReplyKeyboardRemove())
                elif message.text.lower() == "отмена":
                    bot.send_message(message.chat.id, "Ничего со стикером не делаю.", reply_markup = types.ReplyKeyboardRemove())
                else:
                    bot.send_message(message.chat.id, "Ничего со стикером не делаю, неизвестная команда.", reply_markup = types.ReplyKeyboardRemove())

            is_in_list = False
            unique_ids = sql("SELECT unique_id FROM stickers")
            if unique_ids != None:
                for sticker_id in unique_ids:
                    print(sticker_id[0])
                    if message.sticker.file_unique_id in sticker_id[0]:
                        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
                        markup.add(types.KeyboardButton("Удалить"))
                        markup.add(types.KeyboardButton("Отмена"))
                        sticker_in_list = bot.send_message(message.chat.id, "Стикер уже есть в списке стикеров бота, вы хотите удалить его?", reply_markup = markup)
                        bot.register_next_step_handler(sticker_in_list, delete_sticker)
                        is_in_list = True
                        break
            if not is_in_list:
                markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
                for type in sticker_types:
                    markup.add(types.KeyboardButton(type))
                markup.add(types.KeyboardButton("Отмена"))
                sticker_not_in_list = bot.send_message(message.chat.id, "Это новый стикер, к какому типу вы бы отнесли его?", reply_markup = markup)
                bot.register_next_step_handler(sticker_not_in_list, add_sticker)

bot.infinity_polling()
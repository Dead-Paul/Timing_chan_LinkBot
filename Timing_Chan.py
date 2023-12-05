import os
import json
import time
import random
import sqlite3
import telebot
import threading
from telebot import *
from datetime import datetime, timedelta, timezone

def bot_data(get = None, set : dict = None):
    if get != None:
        with open("Bot_Data.json", 'r') as data:
            return json.loads(data.read())[get]
    elif set != None:
        with open("Bot_Data.json", 'r') as was_data:
            new_data = json.loads(was_data.read())
        with open("Bot_Data.json", 'w') as data:
            for key, value in set.items():
                new_data[key] = value
            return json.dump(new_data, data)

bot_token = bot_data("token")
bot = telebot.TeleBot(bot_token, parse_mode = None)
bot_name = bot.get_me().username

creator_id = bot_data("creator_id")

empty_remind = "Пусто ＼(〇_ｏ)／ "
statuses = ["left", "member", "administrator", "creator"]
cancel = ["cancel", "/cancel", f"/cancel@{bot_name.lower()}", "отмена"]

time_difference = bot_data("time_difference")
def get_datetime(add_hours_difference = 0, add_days_difference = 0):
    offset = timedelta(hours = -time.timezone//3600 + time_difference)
    return datetime.now(tz = timezone(offset)) + timedelta(days = add_days_difference, hours = add_hours_difference)

print(f"\nБот включен в {get_datetime().strftime('%H:%M')}. \nДата: {get_datetime().date()}.\n")

def sql(execute_command : str, command_parameters = None):
    base = sqlite3.connect("Bot_Data_Base.db",  detect_types = sqlite3.PARSE_DECLTYPES)
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
sql("CREATE TABLE IF NOT EXISTS birthdays (name TEXT UNIQUE, birthday TIMESTAMP)")

sql("CREATE TABLE IF NOT EXISTS days (day TEXT UNIQUE, is_work_day BOOLEAN)")
sql("CREATE TABLE IF NOT EXISTS rings (start TIMESTAMP, end TIMESTAMP, empty_lesson TEXT UNIQUE)")
sql("CREATE TABLE IF NOT EXISTS lessons (name TEXT UNIQUE, link TEXT, class TEXT, max_grade INTEGER)")
sql("CREATE TABLE IF NOT EXISTS timetable (lesson_id INTEGER, flasher_id INTEGER, remind TEXT)")

sql("CREATE TABLE IF NOT EXISTS stickers (id TEXT, unique_id TEXT UNIQUE, type TEXT)")


def get_sticker(types : list = ["study", "happy", "lovely", "sad", "error", "service", "secret"]):
    type_ids = []
    for type in types:
        for sticker in sql("SELECT id FROM stickers WHERE type = {}".format(f"\"{type}\"")):
            type_ids.append(sticker)
    return random.choice(type_ids)[0]


congratulations = ["Желаем удачи и попутного ветра во всех начинаниях! \nЯркости жизни, душевного тепла, солнечных дней, радостных событий и безмерного счастья!",
                   "Пусть мечты воплотятся в жизнь, успехов и удачи в делах! \nРадостного праздничного дня, исполнения желаний, здоровья и благополучия!",
                   "Желаем здоровья, удачи, любви, везения, мира, добра, улыбок, благополучия. Пусть все мечты исполняются. Пусть жизнь будет долгой и гладкой!",
                   "Пусть твой дом наполняет счастье и тепло, твою душу — гармония и спокойствие. В сердце пускай живет любовь, в мыслях — позитив.",
                   "Пускай сейчас и сегодня все твои желания сбываются. Задуманное тобой реализуется. А удача всегда и во всём преследует тебя.",
                   "Желаем яркого позитивного настроения, высоких достижений, душевной гармонии, процветания, крепкого здоровья, успехов во всём!"]
def celebration():
    while True:
        birthdays = sql("SELECT * FROM birthdays WHERE birthday not NULL")
        birthday_humans = []
        for human in birthdays:
            if human[1].strftime("%m-%d") == datetime(get_datetime().year, get_datetime().month, get_datetime().day).strftime("%m-%d") and \
                human[1].year < get_datetime().year:
                birthday_humans.append(human)
        if len(birthday_humans) > 0:
            for birthday_human in birthday_humans:
                sql("UPDATE birthdays SET birthday = ? WHERE name = ?",
                          (datetime(get_datetime().year, get_datetime().month, get_datetime().day), birthday_human[0]))
                group_id = sql("SELECT id FROM users WHERE access = {} and name = {}".format(1, "\"group\""))[0][0]
                bot.send_message(group_id, f"Сегодня День Рождения у {birthday_human[0]}! \n\n{random.choice(congratulations)}")
                bot.send_sticker(group_id, get_sticker(["happy", "lovely"]))
                print(f"{' ' * 4}Сегодня ({get_datetime().date()}) День Рождения у {birthday_human[0]}!\n")
        else:
            print(f"{' ' * 4}Сегодня ({get_datetime().date()}) ни у кого нет Дня рождения.\n")
        time.sleep((get_datetime(add_days_difference=1).replace(hour=7, minute=0, second=0, microsecond=0) - get_datetime()).seconds)

celebration_tread = threading.Thread(target = celebration)
celebration_tread.start()


def next_work_day_after(weekday : int = 0):
    days = sql("SELECT rowid - 1, day, is_work_day FROM days")
    if weekday < 6:
        weekday += 1
    for day in days[weekday:]:
        if days[day[0]][2]:
            return day[0]
        if day[0] == days[-1][0]:
            for day in days:
                if days[day[0]][2]:
                    return day[0]


def compose_lesson(id: list = [1, 1]):
    lesson = sql("SELECT * FROM lessons WHERE rowid = {}".format(id[0]))
    flasher = sql("SELECT * FROM lessons WHERE rowid = {}".format(id[1]))
    result = {"name" : "", "link" : "", "remind" : empty_remind}
    if lesson != None and flasher != None:
        if flasher[0][0] == sql("SELECT name FROM lessons WHERE rowid = {}".format(1))[0][0]:
            result["name"] = lesson[0][0]
            result["link"] = f" \n\nСсылка на занятие: \n{lesson[0][1]} \n\nСсылка на класс: \n{lesson[0][2]}"
        else:
            result["name"] = f"{lesson[0][0]} / {flasher[0][0]}"
            result["link"] = f" \n\nСсылка на занятие ({lesson[0][0]}): \n{lesson[0][1]} \n\nСсылка на класс: \n{lesson[0][2]}"
            result["link"] += f" \n\nСсылка на занятие ({flasher[0][0]}): \n{flasher[0][1]} \n\nСсылка на класс: \n{flasher[0][2]}"
    return result

def lesson_at(day_time):
    days = sql("SELECT rowid - 1, day, is_work_day FROM days")
    rings = sql("SELECT * FROM rings")

    if not days[day_time.weekday()][2]:
        lesson = compose_lesson([0, 0])
        lesson["is_lesson"] = False
        lesson["name"] = "Сегодня занятий и нет вовсе, отдыхайте..."
        return lesson
    else:
        if rings[0][0].strftime("%H:%M") > day_time.strftime("%H:%M"):
            lesson = compose_lesson([0, 0])
            lesson["is_lesson"] = False
            lesson["name"] = "Занятия ещё не начались, отдохните..."
            return lesson
        elif rings[-1][1].strftime("%H:%M") < day_time.strftime("%H:%M"):
            lesson = compose_lesson([0, 0])
            lesson["is_lesson"] = False
            lesson["name"] = "Занятия уже закончились, отдохните..."
            return lesson
        else:
            for index in range(0, len(rings)):
                if rings[index][0].strftime("%H:%M") <= day_time.strftime("%H:%M") <= rings[index][1].strftime("%H:%M"):
                    lesson = compose_lesson(sql("SELECT * FROM timetable WHERE rowid = {}".format((index + 1) + day_time.weekday() * len(rings)))[0])
                    lesson["remind"] = sql("SELECT remind FROM timetable WHERE rowid = {}".format((index + 1) + day_time.weekday() * len(rings)))[0][0]
                    if lesson["name"] == sql("SELECT name FROM lessons WHERE rowid = {}".format(1))[0][0]:
                        lesson["is_lesson"] = False
                        lesson["name"] = f"{rings[index][2]} нет! \n(´ ∀ ` *) "
                    else:
                        lesson["is_lesson"] = True
                    return lesson
            lesson = compose_lesson([0, 0])
            lesson["is_lesson"] = False
            lesson["name"] = "Сейчас перемена, передохните."
            return lesson


def distribution(announcement : str, remind : str = empty_remind, sticker_types : list = ["service"]):
    id_list = sql("SELECT id, name FROM users WHERE distribution = {} ".format(True))
    if id_list != None:
        print(f"{' ' * 4}Рассылка включена у {len(id_list)} пользователей.")
        for id in id_list:
            try:
                bot.send_message(id[0], announcement)
                if empty_remind not in remind:
                    bot.send_message(id[0], remind)
                try:
                    bot.send_sticker(id[0], get_sticker(sticker_types))
                except:
                    bot.send_message(id[0], "У меня не получилось отправить стикер. \n(♡μ_μ) ")
            except:
                sql("UPDATE users SET distribution = {} WHERE id = {}".format(False, id[0]))
    else:
        print(f"{' ' * 4}Рассылка выключена у всех пользователей...")

def lessons_distribution():
    while True:
        print(f"{' ' * 4}Рассылка включена в {get_datetime().strftime('%H:%M')} \n")
        rings = sql("SELECT * FROM rings")
        if sql("SELECT is_work_day FROM days WHERE rowid - 1 = {}".format(get_datetime().weekday()))[0][0]:
            if rings[0][0].strftime("%H:%M") > (get_datetime() + timedelta(minutes = 4)).strftime("%H:%M"):
                time.sleep((get_datetime().replace(hour=(rings[0][0] - timedelta(minutes=4)).hour, minute=(rings[0][0] - timedelta(minutes=4)).minute,
                                                                        second=0, microsecond=0) - get_datetime()).seconds)
            elif rings[-1][1].strftime("%H:%M") < get_datetime().strftime("%H:%M"):
                time.sleep((get_datetime(add_days_difference=1).replace(hour=(rings[0][0] - timedelta(minutes=4)).hour,
                                                                        minute=(rings[0][0] - timedelta(minutes=4)).minute,
                                                                        second=0, microsecond=0) - get_datetime()).seconds)
            for index in range(0, len(rings)):
                if rings[index][0].strftime("%H:%M") == get_datetime((1 / 60) * 3).strftime("%H:%M"):
                    lesson = lesson_at(get_datetime((1 / 60) * 4))
                    if lesson["is_lesson"] or index + 1 < len(rings):
                        if lesson["is_lesson"]:
                            distribution(f"{lesson['name']} {lesson['link']}", lesson["remind"], ["study", "sad"])
                            print(f"\n{' ' * 8}{index + 1} занятие началось, время: {get_datetime().strftime('%H:%M')}\n")
                        elif not lesson["is_lesson"]:
                            distribution(f"{lesson['name']} {lesson['link']}", lesson["remind"], ["study", "sad"])
                            print(f"\n{' ' * 8}{index + 1} занятия нет, время: {get_datetime().strftime('%H:%M')}\n")
                        time.sleep((get_datetime().replace(hour = (rings[index][1] - timedelta(minutes = 1)).hour,
                                                           minute = (rings[index][1] - timedelta(minutes = 1)).minute,
                                                           second = 0, microsecond = 0) - get_datetime()).seconds)
                    else:
                        distribution(f"Учебный день закончился, можете отдохнуть!", empty_remind, ["happy", "lovely"])
                        print(f"{' ' * 4}Рассылка выключена в {get_datetime().strftime('%H:%M')} \n")
                        time.sleep((get_datetime(add_days_difference = 1).replace(hour = (rings[0][0] - timedelta(minutes = 4)).hour,
                                                                                  minute = (rings[0][0] - timedelta(minutes = 4)).minute,
                                                                                  second = 0, microsecond = 0) - get_datetime()).seconds)
                elif rings[index][1].strftime("%H:%M") == get_datetime().strftime("%H:%M"):
                    sql("UPDATE timetable SET remind = {} WHERE rowid = {}".format(f"\"{empty_remind}\"",
                                                                                   (index + 1) + get_datetime().weekday() * len(rings)))
                    print(f"\n{' ' * 8}{index + 1} занятие закончилось, время: {get_datetime().strftime('%H:%M')}\n")
                    if index + 1 >= len(rings):
                        distribution(f"Учебный день закончился, можете отдохнуть!", empty_remind, ["study", "sad"])
                        print(f"{' ' * 4}Учебный день закончился в {get_datetime().strftime('%H:%M')} \n")
                        time.sleep((get_datetime(add_days_difference = 1).replace(hour = (rings[0][0] - timedelta(minutes = 4)).hour,
                                                                                  minute = (rings[0][0] - timedelta(minutes = 4)).minute,
                                                                                  second = 0, microsecond = 0) - get_datetime()).seconds)
                    else:
                        lesson = lesson_at(rings[index + 1][0].replace(year = get_datetime().year, month = get_datetime().month, day = get_datetime().day) + timedelta(minutes = 1))
                        if lesson["is_lesson"]:
                            distribution(f"Далее будет {lesson['name']} \nВ {rings[index + 1][0].strftime('%H:%M')}.", lesson["remind"],
                                         ["study", "sad"])
                            time.sleep((get_datetime().replace(hour = (rings[index + 1][0] - timedelta(minutes = 4)).hour,
                                                               minute = (rings[index + 1][0] - timedelta(minutes = 4)).minute,
                                                               second = 0, microsecond = 0) - get_datetime()).seconds)
                        elif index + 2 < len(rings) and lesson_at(rings[index + 2][0].replace(year = get_datetime().year, month = get_datetime().month, day = get_datetime().day) + timedelta(minutes = 1))["is_lesson"]:
                            distribution(f"{lesson['name']} \nОтдыхайте до {rings[index + 2].strftime('%H:%M')}.", lesson["remind"],
                                         ["study", "sad"])
                            time.sleep((get_datetime().replace(hour = (rings[index + 1][1] - timedelta(minutes = 1)).hour,
                                                               minute = (rings[index + 1][1] - timedelta(minutes = 1)).minute,
                                                               second = 0, microsecond = 0) - get_datetime()).seconds)
                        else:
                            distribution(lesson["name"], lesson["remind"], ["study", "sad"])
                            time.sleep((get_datetime().replace(hour = (rings[index + 1][0] - timedelta(minutes = 4)).hour,
                                                               minute = (rings[index + 1][0] - timedelta(minutes = 4)).minute,
                                                               second = 0, microsecond = 0) - get_datetime()).seconds)
            time.sleep(30)
        else:
            time.sleep((get_datetime(add_days_difference = 1).replace(hour = (rings[0][0] - timedelta(minutes = 4)).hour,
                                                                      minute = (rings[0][0] - timedelta(minutes = 4)).minute,
                                                                      second = 0, microsecond = 0) - get_datetime()).seconds)

lesson_distribution_thread = threading.Thread(target = lessons_distribution)
lesson_distribution_thread.start()

def update_user(message):
    status = bot.get_chat_member(chat_id = sql("SELECT id FROM users WHERE access = {} and name = {}".format(1, f"\"{bot_data('group_title')}\""))[0][0],
                                 user_id = message.from_user.id).status
    if status in statuses:
        if message.from_user.id == creator_id:
            status_index = 3
        else:
            status_index = statuses.index(status)
    else:
        status_index = 0
    if sql("INSERT INTO users VALUES ({}, {}, {}, {})".format(message.from_user.id, f"\"{message.from_user.username}\"", status_index, False)) == "ERROR":
            sql("UPDATE users SET name = {}, access = {} WHERE id = {}".format(f"\"{message.from_user.username}\"", status_index, message.from_user.id))
    return status_index

@bot.message_handler(commands = ["start"])
def start_msg(message):

    if str(message.chat.id)[0] != '-':
        if update_user(message) < 2:
            bot.send_message(message.chat.id, f"Приветствую, {message.from_user.first_name}! \n٩(◕‿◕｡)۶ ")
            bot.send_sticker(message.chat.id, get_sticker(["study"]))
        else:
            bot.send_message(message.chat.id, f"Приветствую, {message.from_user.first_name}! \nヽ(♡‿♡)ノ ")
            bot.send_sticker(message.chat.id, get_sticker(["lovely"]))

    elif str(message.chat.id)[0] == '-':
        if bot.get_chat(message.chat.id).title == bot_data("group_title"):
            if sql("INSERT INTO users VALUES ({}, {}, {}, {})".format(message.chat.id, f"\"{bot.get_chat(message.chat.id).title}\"", 1, False)) != "ERROR":
                bot.send_message(message.chat.id, "Приветствую, вы моя основная группа! \n♡( ◡‿◡ ) ")
                bot.send_message(message.chat.id, "Все, кто назначен админами в этой группе - автоматически являются админами бота (меня);\n"
                                                       "Создатель этой группы - автоматически становится главным админом (создателем бота); \n"
                                                       "Всё это надо для команд, которые созданы специально для админов. \n\n"
                                                       "Вообще это единственное зачем боту (мне) нужна эта группа.")
            else:
                bot.send_message(message.chat.id, f"Снова приветствую, {bot.get_chat(message.chat.id).title}! \nヽ(♡‿♡)ノ  ")
            bot.send_sticker(message.chat.id, get_sticker(["lovely"]))
        else:
            sql("INSERT INTO users VALUES ({}, {}, {}, {})".format(message.chat.id, f"\"{bot.get_chat(message.chat.id).title}\"", 0, False))
            bot.send_message(message.chat.id, f"Приветствую, {bot.get_chat(message.chat.id).title}! \n( 〃▽〃) ")
            bot.send_sticker(message.chat.id, get_sticker(["study"]))

    def distribution_act(message):
        if message.text.lower() not in cancel:
            if message.text == "Делать":
                sql("UPDATE users SET distribution = {} WHERE id = {}".format(True, message.chat.id))
                bot.send_message(message.chat.id, "Tеперь сообщения о начале пар будут приходить Вам в этот чат. \nヽ(*・ω・)ﾉ \
                                \n\nВы всегда можете изменить своё решение!", reply_markup = types.ReplyKeyboardRemove())
                bot.send_sticker(message.chat.id, get_sticker(["happy"]))
            elif message.text == "Не Делать":
                sql("UPDATE users SET distribution = {} WHERE id = {}".format(False, message.chat.id))
                bot.send_message(message.chat.id, "Сообщения о начале пар не будут приходить вам в этот чат. \n(*μ_μ) \
                                \n\nHо Вы всегда можете изменить своё решение.", reply_markup = types.ReplyKeyboardRemove())
                bot.send_sticker(message.chat.id, get_sticker(["sad"]))
            else:
                bot.send_message(message.chat.id, "Я ждала от Вас не такого сообщения. \n(｡T ω T｡)  \n\nOставляю рассылку такой, какой она была."
                                 , reply_markup = types.ReplyKeyboardRemove())
                bot.send_sticker(message.chat.id, get_sticker(["error"]))
        elif message.text.lower() in cancel:
            bot.send_message(message.chat.id, "Рассылка останется прежней или заданной по умолчанию. \n(＃￣ω￣) ",
                             reply_markup = types.ReplyKeyboardRemove())

    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
    markup.add(types.KeyboardButton("Делать"))
    markup.add(types.KeyboardButton("Не Делать"))
    question = bot.send_message(message.chat.id, "Для начала я хочу узнать, присылать ли Вам сообщения о парах в этот чат? \n(´｡• ω •｡`) \
               \n\nЕсли у Вас возникли вопросы, то после того как Вы ответите - можно воспользоваться /FAQ .", reply_markup = markup)
    bot.register_next_step_handler(question, distribution_act)

    update_user(message)

@bot.message_handler(commands = ["rings"])
def rings_msg(message):
    rings_schedule = []
    for lesson_time in sql("SELECT rowid, * FROM rings"):
        rings_schedule.append(f"\n{lesson_time[0]} {lesson_time[-1][lesson_time[-1].index(' '):]}: {lesson_time[1].strftime('%H:%M')} - {lesson_time[2].strftime('%H:%M')}")
    bot.send_message(message.chat.id, ";".join(rings_schedule) + ".")
    bot.send_sticker(message.chat.id, get_sticker(["happy"]))

    update_user(message)


@bot.message_handler(commands = ["timetable", "today", "tommorow"])
def timetable_msg(message):
    days = sql("SELECT rowid - 1, day, is_work_day FROM days")
    rings = sql("SELECT rowid, * FROM rings")

    def timetable_for(day : int):
        day_timetable = []
        start_from = day * len(rings)
        timetable_ids = sql("SELECT * FROM timetable WHERE {} < rowid and rowid <= {}".format(start_from, start_from + len(rings)))
        for id in range(0, len(timetable_ids)):
            day_timetable.append(f"\n{' ' * 4}{id + 1}. {compose_lesson(timetable_ids[id])['name']}")
        return f"{' ' * 2}{days[day][1]}:" + ";".join(day_timetable) + "."

    if "timetable" in message.text:
        timetable = ["Расписание:"]
        for day in days:
            if day[2]:
                timetable.append(timetable_for(day[0]))
            else:
                timetable.append(f"{' ' * 2}{day[1]}: \n{' ' * 4}Выходной! \n{' ' * 4}<(￣︶￣)>   ")
        bot.send_message(message.chat.id, "\n\n".join(timetable))
        bot.send_sticker(message.chat.id, get_sticker(["happy", "sad"]))

    elif "today" in message.text:
        today = get_datetime().weekday()
        if days[today][2]:
            bot.send_message(message.chat.id, timetable_for(today))
            bot.send_sticker(message.chat.id, get_sticker(["sad"]))
        else:
            bot.send_message(message.chat.id, f"Сегодня выходной, отдыхайте. \nヽ(*・ω・)ﾉ  ")
            bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))

    elif "tommorow" in message.text:
        tommorow = get_datetime(add_days_difference = 1).weekday()
        if days[tommorow][2]:
            bot.send_message(message.chat.id, timetable_for(tommorow))
            bot.send_sticker(message.chat.id, get_sticker(["sad"]))
        else:
            bot.send_message(message.chat.id, f"Завтра можно отдохнуть, следующий учебный день будет:")
            bot.send_message(message.chat.id, timetable_for(next_work_day_after(tommorow)))
            bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))

    update_user(message)



@bot.message_handler(commands = ["edit_timetable"])
def edit_timetable_msg(message):
    rings = sql("SELECT rowid, * FROM rings")

    def edit_remind(message, day, number):
        if str(message.text).lower() not in cancel:
            if message.text.lower() == "удалить":
                if sql("UPDATE timetable SET remind = {} WHERE rowid = {}".format(f"\"{empty_remind}\"", number + day * len(rings))) != "ERROR":
                    bot.send_message(message.chat.id, f"Редактирование завершено! Текст напоминания удалён. \n٩(◕‿◕｡)۶ ",
                                     reply_markup = types.ReplyKeyboardRemove())
                else:
                    bot.send_message(message.chat.id, "Не удалось удалить текст напоминания, попробуйте ещё раз. \n(＞﹏＜) \
                                     \n\nЕсли ошибка повторится, то попросите помощи у создателя через команду /support.")
            else:
                if sql("UPDATE timetable SET remind = {} WHERE rowid = {}".format(f"\"{message.text}\"", number + day * len(rings))) != "ERROR":
                    bot.send_message(message.chat.id, "Редактирование завершено! Текст напоминания изменён. \n٩(◕‿◕｡)۶",
                                     reply_markup = types.ReplyKeyboardRemove())
                    lesson_now = lesson_at(get_datetime())
                    lesson_id = sql("SELECT lesson_id FROM timetable WHERE rowid = {}".format(number + day * len(rings)))[0][0]
                    if lesson_now["is_lesson"] and compose_lesson([lesson_id, 1])["name"] in lesson_now["name"]:
                        distribution(f"К {lesson_now['name']} добавлено новое напоминание:", lesson_now["remind"], ["sad", "happy"])
                        bot.send_message(message.chat.id, "Эта пара проходит сейчас - поэтому я напоминание разослано всем участникам рассылки. \n(.❛ ᴗ ❛.) ")
                else:
                    bot.send_message(message.chat.id, "Не удалось отредактировать текст напоминания,\
                                     \nотправляйте только текстовые сообщения и попробуйте ещё раз. \n(＞﹏＜) \
                                     \n\nЕсли ошибка повторится, то попросите помощи у создателя через команду /support.",
                                     reply_markup = types.ReplyKeyboardRemove())
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Хорошо, напоминания не редактирую. \n(￣ヘ￣) ", reply_markup = types.ReplyKeyboardRemove())

    def new_remind(message, day):
        if str(message.text).lower() not in cancel:
            if message.text[0:1].isnumeric():
                number = int(message.text[0:1])
                if 0 < number <= len(rings):
                    previous_remind = sql("SELECT remind FROM timetable WHERE rowid = {}".format(number + day * len(rings)))[0][0]
                    id = sql("SELECT lesson_id, flasher_id FROM timetable WHERE rowid = {}".format(number + day * len(rings)))[0]
                    lesson = compose_lesson(id)
                    bot.send_message(message.chat.id, f"Сейчас напоминание к {message.text[2:]}: \n{previous_remind} \n\n٩(｡•́‿•̀｡)۶ ")
                    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
                    markup.add(types.KeyboardButton("Удалить"))
                    markup.add(types.KeyboardButton("Отмена"))
                    ask_text = bot.send_message(message.chat.id, f"Теперь напишите новый текст напоминания, \
                                                               \n(чтоб удалить напоминание нажмите на кнопку \"Удалить\"). \
                                                               \nЕсли передумали, то /cancel или Отмена.", reply_markup = markup)
                    bot.register_next_step_handler(ask_text, edit_remind, day, number)
                else:
                    bot.send_message(message.chat.id, "Не правильно указан номер занятия, поэтому редактирование отменено. \n(--_--) ",
                                     reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, "В сообщении не указан номер занятия, поэтому редактирование отменено. \n<(￣ ﹌ ￣)> ",
                                 reply_markup = types.ReplyKeyboardRemove())
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Хорошо, напоминания не редактирую. \n(눈_눈) ", reply_markup = types.ReplyKeyboardRemove())

    def edit_lesson(message, lesson_type, day, number):
        if str(message.text).lower() not in cancel:
            lesson_id = sql("SELECT rowid FROM lessons WHERE name = {}".format(f"\"{str(message.text)}\""))
            if lesson_id != "ERROR":
                if lesson_id[0][0] != "" and lesson_id != None:
                    if sql("UPDATE timetable SET {} = {} WHERE rowid = {}".format(lesson_type, lesson_id[0][0], int(number) + int(day) * len(rings))) != "ERROR":
                        bot.send_message(message.chat.id, "Изменения внесены, Редактирование завершено! \n(￢‿￢ ) ",
                                         reply_markup = types.ReplyKeyboardRemove())
                        if sql("SELECT remind FROM timetable WHERE rowid = {}".format(int(number) + int(day) * len(rings)))[0][0] != empty_remind:
                            bot.send_message(message.chat.id, "Возможно напоминание к этому занятию не актуально! \
                                                                  \nВы хотите удалить, или изменить его? \
                                                                  \n(←_←) ",
                                             reply_markup=types.ReplyKeyboardRemove())
                            message.text = str(number)
                            new_remind(message, day)
                    else:
                        bot.send_message(message.chat.id, "Ошибка в базе данных. Редактирование не было завершено! \n[ ± _ ± ] ",
                                         reply_markup = types.ReplyKeyboardRemove())
                else:
                    bot.send_message(message.chat.id, "Не поняла задачи, поэтому отменяю редактирование... \n(--_--)",
                                     reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message( message.chat.id, "Не удалось завершить редактирование, так как была получена неправильная информацию. \
                                 \n\nПожалуйста нажимайте на кнопки с заготовленными ответами, а не вводите текст вручную. \
                                 \n\nЕсли всё было выполнено корректно, но ошибка остаётся - обратитесь к создателю через команду /support.",
                                  reply_markup = types.ReplyKeyboardRemove())
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def select_lesson_name(message, lesson_type, day):
        if message.text[0].isnumeric():
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for lesson in sql("SELECT name FROM lessons ORDER BY rowid"):
                markup.add(types.KeyboardButton(lesson[0]))
            markup.add(types.KeyboardButton("Отмена"))
            ask_new_name = bot.send_message(message.chat.id, "Выберете новое название:", reply_markup=markup)
            bot.register_next_step_handler(ask_new_name, edit_lesson, lesson_type, day, message.text[0])
        else:
            bot.send_message(message.chat.id, "Пожалуйста, нажимайте на кнопки с заготовленными ответами, а не вводите текст вручную.\n(눈_눈)",
                             reply_markup=types.ReplyKeyboardRemove())

    def select_lesson_day(message, lesson_type):
        if message.text.lower() not in cancel:
            day = sql("SELECT rowid - 1 FROM days WHERE day = {}".format(f"\"{message.text}\""))[0][0]
            if str(day).isnumeric():
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                for number in range(1, len(rings) + 1):
                    lesson_name = sql("SELECT name FROM lessons WHERE rowid = {}".format(
                        sql("SELECT lesson_id FROM timetable WHERE rowid = {}".format(number + day * len(rings)))[0][0]))[0][0]
                    flasher_name = sql("SELECT name FROM lessons WHERE rowid = {}".format(
                        sql("SELECT flasher_id FROM timetable WHERE rowid = {}".format(number + day * len(rings)))[0][0]))[0][0]
                    markup.add(types.KeyboardButton(f"{str(number)}) {lesson_name}/{flasher_name}"))
                markup.add(types.KeyboardButton("Отмена"))
                ask_number = bot.send_message(message.chat.id, "Выберете номер:", reply_markup=markup)
                if lesson_type == "lesson_id" or lesson_type == "flasher_id":
                    bot.register_next_step_handler(ask_number, select_lesson_name, lesson_type, day)
                elif lesson_type == "remind":
                    bot.register_next_step_handler(ask_number, new_remind, day)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, нажимайте на кнопки с заготовленными ответами, а не вводите текст вручную.\n(눈_눈)",
                                 reply_markup = types.ReplyKeyboardRemove())
        elif message.text.lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def edit_link(message, link_type, lesson_id):
        if message.text.lower() not in cancel:
            if sql("UPDATE lessons SET {} = {} WHERE rowid = {}".format(link_type, f"\"{message.text}\"", lesson_id)) != "ERROR":
                bot.send_message( message.chat.id, f"Редактирование завершено! Ccылка изменена. \n(￣▽￣*)ゞ", reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message( message.chat.id, "Не удалось завершить редактирование из-за ошибки ввода. \
                                 \n\nПожалуйста не отправляйте в ссылку что-либо кроме текста, \
                                 \n\nесли ошибка останется - обратитесь к создателю через команду /support.",
                                  reply_markup = types.ReplyKeyboardRemove())
        elif message.text.lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def new_link(message, link_type):
        if str(message.text).lower() not in cancel:
            lesson_id = sql("SELECT rowid FROM lessons WHERE name = {}".format(f"\"{message.text}\""))
            if lesson_id != "ERROR":
                if lesson_id[0][0] != "" and lesson_id != None:
                    previous_link = sql("SELECT {} FROM lessons WHERE rowid = {}".format(link_type, lesson_id[0][0]))[0][0]
                    bot.send_message(message.chat.id, f"Предыдущая ссылка к этой паре была: {previous_link} . \n(o_O) ")
                    ask_new_link = bot.send_message(message.chat.id, f"Пришлите мне новую ссылку к {message.text}:", reply_markup = types.ReplyKeyboardRemove())
                    bot.register_next_step_handler(ask_new_link, edit_link, link_type, lesson_id[0][0])
                else:
                    bot.send_message(message.chat.id, "Занятие не найдено, отменяю редактирование... \n(⊙_⊙) ", reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message( message.chat.id, "Не удалось завершить редактирование, так как была получена неправильная информацию. \
                                 \n\nПожалуйста нажимайте на кнопки с заготовленными ответами, а не вводите текст вручную. \
                                 \n\nЕсли всё было выполнено корректно, но ошибка остаётся - обратитесь к создателю через команду /support.",
                                  reply_markup = types.ReplyKeyboardRemove())
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def edit_grade(message, lesson_id):
        if message.text.lower() not in cancel:
            if message.text.isnumeric():
                if sql("UPDATE lessons SET max_grade = {} WHERE rowid = {}".format(message.text, lesson_id)) != "ERROR":
                    bot.send_message( message.chat.id, f"Редактирование завершено! Максимальная оценка изменена. \n(￣▽￣*)ゞ",
                                      reply_markup = types.ReplyKeyboardRemove())
                else:
                    bot.send_message( message.chat.id, "Не удалось завершить редактирование из-за ошибки базы данных. \
                                     \n\nПопробуйте ещё раз, \
                                     \n\nесли ошибка останется - обратитесь к создателю через команду /support.",
                                      reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, "Вводите оценку как число. Если оценка в буквенном виде, то отправьте \"0\". \n(￣～￣　) ",
                                 reply_markup=types.ReplyKeyboardRemove())

        elif message.text.lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def new_grade(message):
        if str(message.text).lower() not in cancel:
            lesson_id = sql("SELECT rowid FROM lessons WHERE name = {}".format(f"\"{message.text[:message.text.index('(') - 1]}\""))
            if lesson_id != "ERROR":
                if lesson_id[0][0] != "" and lesson_id != None:
                    ask_new_grade = bot.send_message(message.chat.id, f"Пришлите мне новую максимальную оценку к {message.text}:",
                                                     reply_markup = types.ReplyKeyboardRemove())
                    bot.register_next_step_handler(ask_new_grade, edit_grade, lesson_id[0][0])
                else:
                    bot.send_message(message.chat.id, "Занятие не найдено, отменяю редактирование... \n(⊙_⊙) ", reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message( message.chat.id, "Не удалось завершить редактирование, так как была получена неправильная информацию. \
                                 \n\nПожалуйста нажимайте на кнопки с заготовленными ответами, а не вводите текст вручную. \
                                 \n\nЕсли всё было выполнено корректно, но ошибка остаётся - обратитесь к создателю через команду /support.",
                                  reply_markup = types.ReplyKeyboardRemove())
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def switch_day(message):
        if str(message.text).lower() not in cancel:
            try:
                day = int(sql("SELECT rowid - 1 FROM days WHERE day = {}".format(f"\"{message.text[:message.text.index('(') - 1]}\""))[0][0])
                if sql("SELECT is_work_day FROM days WHERE rowid - 1 = {}".format(day))[0][0]:
                    if sql("UPDATE days SET is_work_day = {} WHERE rowid - 1 = {}".format(False, day)) != "ERROR":
                        bot.send_message(message.chat.id, f"Теперь {message.text[:message.text.index('(') - 1]} выходной! \n╰(*´︶`*)╯♡  ",
                                         reply_markup = types.ReplyKeyboardRemove())
                    else:
                        bot.send_message( message.chat.id, "Не удалось завершить редактирование из-за ошибки базы данных. \
                                         \n\nПопробуйте ещё раз, \
                                         \n\nесли ошибка останется - обратитесь к создателю через команду /support.",
                                          reply_markup = types.ReplyKeyboardRemove())
                else:
                    if sql("UPDATE days SET is_work_day = {} WHERE rowid - 1 = {}".format(True, day)) != "ERROR":
                        bot.send_message(message.chat.id, f"Теперь {message.text[:message.text.index('(') - 1]} рабочий... \n(*´ー`)ﾉ ",
                                         reply_markup = types.ReplyKeyboardRemove())
                    else:
                        bot.send_message( message.chat.id, "Не удалось завершить редактирование из-за ошибки базы данных. \
                                         \n\nПопробуйте ещё раз, \
                                         \n\nесли ошибка останется - обратитесь к создателю через команду /support.",
                                          reply_markup = types.ReplyKeyboardRemove())
            except:
                bot.send_message( message.chat.id, "Не удалось завершить редактирование, так как была получена неправильная информацию. \
                                 \n\nПожалуйста нажимайте на кнопки с заготовленными ответами, а не вводите текст вручную. \
                                 \n\nЕсли всё было выполнено корректно, но ошибка остаётся - обратитесь к создателю через команду /support.",
                                  reply_markup = types.ReplyKeyboardRemove())

        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def edit_lesson_name(message, lesson_id):
        if message.text.lower() not in cancel:
            if sql("UPDATE lessons SET name = {} WHERE rowid = {}".format(f"\"{message.text}\"", lesson_id)) != "ERROR":
                    bot.send_message( message.chat.id, f"Редактирование завершено! Название изменено. \n(￣▽￣*)ゞ", reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message( message.chat.id, "Не удалось завершить редактирование из-за ошибки ввода. \
                                 \n\nПожалуйста не отправляйте в название что-либо кроме текста, \
                                 \n\nесли ошибка останется - обратитесь к создателю через команду /support.")
        elif message.text.lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def new_lesson_name(message):
        if str(message.text).lower() not in cancel:
            lesson_id = sql("SELECT rowid FROM lessons WHERE name = {}".format(f"\"{message.text}\""))
            if lesson_id != "ERROR":
                if lesson_id[0][0] != "" and lesson_id != None:
                    ask_new_lesson_name = bot.send_message(message.chat.id, f"Пришлите мне новое название \"{message.text}\":", reply_markup = types.ReplyKeyboardRemove())
                    bot.register_next_step_handler(ask_new_lesson_name, edit_lesson_name, lesson_id[0][0])
                else:
                    bot.send_message(message.chat.id, "Занятие не найдено, отменяю редактирование... \n(⊙_⊙) ", reply_markup = types.ReplyKeyboardRemove())
            else:
                bot.send_message( message.chat.id, "Не удалось завершить редактирование, так как была получена неправильная информацию. \
                                 \n\nПожалуйста нажимайте на кнопки с заготовленными ответами, а не вводите текст вручную. \
                                 \n\nЕсли всё было выполнено корректно, но ошибка остаётся - обратитесь к создателю через команду /support.")
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    def select_action(message):
        if str(message.text).lower() not in cancel:

            if "Расписание" in message.text or "Напоминание" in message.text:
                if "(основное)" in message.text:
                    lesson_type = "lesson_id"
                elif "(мигалки)" in message.text:
                    lesson_type = "flasher_id"
                elif "Напоминание" in message.text:
                    lesson_type = "remind"

                markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
                for day in sql("SELECT day, is_work_day FROM days"):
                    if day[1]:
                        markup.add(types.KeyboardButton(day[0]))
                markup.add(types.KeyboardButton("Отмена"))
                ask_day = bot.send_message(message.chat.id, "Выберете день:", reply_markup = markup)
                bot.register_next_step_handler(ask_day, select_lesson_day, lesson_type)

            elif "Ссылку" in message.text or "Максимальную оценку" in message.text:
                if "(на занятие)" in message.text:
                    link_type = "link"
                elif "(на класс)" in message.text:
                    link_type = "class"
                elif "Максимальную оценку" in message.text:
                    link_type = "max_grade"

                markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
                for lesson in sql("SELECT name, max_grade FROM lessons ORDER BY rowid"):
                    if link_type == "max_grade":
                        markup.add(types.KeyboardButton(f"{lesson[0]} (макс. балл: {lesson[1]})"))
                    else:
                        markup.add(types.KeyboardButton(lesson[0]))
                markup.add(types.KeyboardButton("Отмена"))
                ask_name = bot.send_message(message.chat.id, "Выберете название:", reply_markup=markup)
                if link_type == "max_grade":
                    bot.register_next_step_handler(ask_name, new_grade)
                else:
                    bot.register_next_step_handler(ask_name, new_link, link_type)

            elif "Название" in message.text:
                markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
                for lesson in sql("SELECT name FROM lessons ORDER BY rowid"):
                    markup.add(types.KeyboardButton(lesson[0]))
                markup.add(types.KeyboardButton("Отмена"))
                ask_name = bot.send_message(message.chat.id, "Выберете название:", reply_markup=markup)
                bot.register_next_step_handler(ask_name, new_lesson_name)

            elif "День" in message.text:
                markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
                for day in sql("SELECT day, is_work_day FROM days"):
                    if day[1]:
                        markup.add(types.KeyboardButton(f"{day[0]} (Рабочий)"))
                    else:
                        markup.add(types.KeyboardButton(f"{day[0]} (Выходной)"))
                markup.add(types.KeyboardButton("Отмена"))
                ask_day = bot.send_message(message.chat.id, "Выберете день:", reply_markup = markup)
                bot.register_next_step_handler(ask_day, switch_day)

            else:
                bot.send_message(message.chat.id, "Пожалуйста, нажимайте на кнопки с заготовленными ответами, а не вводите текст вручную.\n(눈_눈)",
                                 reply_markup = types.ReplyKeyboardRemove())
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Ничего не меняю. \n(￣～￣　) ", reply_markup = types.ReplyKeyboardRemove())

    if str(message.chat.id)[0] != '-':
        if update_user(message) >= 2:
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            markup.add(types.KeyboardButton("Расписание (основное)"))
            markup.add(types.KeyboardButton("Расписание (мигалки)"))
            markup.add(types.KeyboardButton("Напоминание"))
            markup.add(types.KeyboardButton("Ссылку (на занятие)"))
            markup.add(types.KeyboardButton("Ссылку (на класс)"))
            markup.add(types.KeyboardButton("Название занятия"))
            markup.add(types.KeyboardButton("Максимальную оценку"))
            markup.add(types.KeyboardButton("День (выходной/рабочий)"))
            markup.add(types.KeyboardButton("Отмена"))
            edit_question = bot.send_message(message.chat.id, "Что отредактируем?", reply_markup = markup)
            bot.register_next_step_handler(edit_question, select_action)
            bot.send_sticker(message.chat.id, get_sticker(["service"]))
        else:
            bot.send_message(message.chat.id, "Вы не админ, а потому не можете редактировать расписание. \n(︶︹︺) ")
            bot.send_sticker(message.chat.id, get_sticker(["sad"]))
    elif str(message.chat.id)[0] == '-':
        bot.send_message(message.chat.id, f"Вы не можете редактровать расписание в чате группы. \n(＞_＜) \
                                        \n\nЧтобы использовать все доступные комманды напишите в лс боту: @{bot_name}")



await_to_answer = {}
def answer_to_creator_message(message):
    for creator in [sql("SELECT id FROM users WHERE access = {}".format(3))[0][0], creator_id]:
        if message.from_user.id in await_to_answer[creator]:
            await_to_answer[creator].remove(message.from_user.id)
            bot.send_message(creator, f"Ответ на ваше сообщение от: @{message.from_user.username}.")
            bot.forward_message(creator_id, message.chat.id, message.message_id)
            break

recipients = ["В Группу", "Пользователю", "Всем Админам", "Всем Пользователям"]
@bot.message_handler(commands = ["write"])
def write_msg(message):
    recipient_ids = []

    def message_to_user(message):
        if str(message.text).lower() not in cancel:
            sended = 0
            not_sended = 0
            if update_access == 3:
                await_to_answer[message.from_user.id] = set()
            for recipient in recipient_ids:
                try:
                    if update_access == 3:
                        bot.copy_message(recipient[0][0], message.chat.id, message.message_id)
                        if str(recipient[0][0])[0] != "-":
                            await_to_answer[message.from_user.id].add(recipient[0][0])
                            bot.register_next_step_handler(bot.send_sticker(recipient[0][0], get_sticker(["happy", "sad", "lovely"])),
                                                           answer_to_creator_message)
                    else:
                        bot.copy_message(recipient[0][0], message.chat.id, message.message_id)
                    sended += 1
                except:
                    not_sended += 1
            if len(recipient_ids) > 1:
                bot.send_message(message.chat.id, f"Ваше сообщение отправлено {str(sended)} пользователям из {str(sended + not_sended)}. \
                                                \n\nНеудачных отправок: {str(not_sended)}.", reply_markup = types.ReplyKeyboardRemove())
            elif sended == len(recipient_ids):
                bot.send_message(message.chat.id, "Сообщение отправлено успешно. \n(* ^ ω ^) ")
                bot.send_sticker(message.chat.id, get_sticker(["service", "lovely"]))
            elif not_sended == len(recipient_ids):
                bot.send_message(message.chat.id, "Не получилось отправить сообщение, вероятно пользователь заблокировал бота. \n(μ_μ) ")
                bot.send_sticker(message.chat.id, get_sticker(["sad", "lovely"]))
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Отменяю отправку. \n(μ_μ) ", reply_markup = types.ReplyKeyboardRemove())

    def message_to_user_name(message):
        if str(message.text).lower() not in cancel:
            user_id = sql("SELECT id FROM users WHERE name = {}".format(f"\"{message.text[1:]}\""))
            if user_id != None:
                recipient_ids.append(user_id)
                ask_text = bot.send_message(message.chat.id, f"Следующее ваше сообщение я отправлю {message.text}. Если передумали - /cancel )",
                                            reply_markup = types.ReplyKeyboardRemove())
                bot.register_next_step_handler(ask_text, message_to_user)
            else:
                bot.send_message(message.chat.id, "Пользователь не найден в моей базе данных, убидитесь, что вы правильно написали его ник.",
                                  reply_markup = types.ReplyKeyboardRemove())
                bot.send_sticker(message.chat.id, get_sticker(["sad", "error"]))
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Отменяю отправку. \n(μ_μ) ", reply_markup = types.ReplyKeyboardRemove())

    def message_to_group_name(message):
        if str(message.text).lower() not in cancel:
            group_id = sql("SELECT id FROM users WHERE name = {}".format(f"\"{message.text}\""))
            if group_id != None:
                recipient_ids.append(group_id)
                ask_text = bot.send_message(message.chat.id, f"Следующее ваше сообщение я отправлю в \"{message.text}\": ",
                                            reply_markup = types.ReplyKeyboardRemove())
                bot.register_next_step_handler(ask_text, message_to_user)
            else:
                bot.send_message(message.chat.id, "Группа не найдена в моей базе данных, убидитесь, что вы правильно написали её название.",
                                  reply_markup = types.ReplyKeyboardRemove())
                bot.send_sticker(message.chat.id, get_sticker(["sad", "error"]))
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Отменяю отправку. \n(μ_μ) ", reply_markup = types.ReplyKeyboardRemove())

    def message_to(message):
        if str(message.text).lower() not in cancel:
            if message.text in recipients or str(message.text)[0] == '@':
                nonlocal recipient_ids
                if message.text == recipients[0]:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    groups = sql("SELECT name FROM users WHERE id < 0")
                    for group in groups:
                        markup.add(types.KeyboardButton(group[0]))
                    markup.add(types.KeyboardButton("Отмена"))
                    ask_recipient = bot.send_message(message.chat.id, f"Выберите имя группы:", reply_markup = markup)
                    bot.register_next_step_handler(ask_recipient, message_to_group_name)
                elif message.text == recipients[1]:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    users = sql("SELECT name FROM users WHERE id >= 0")
                    for user in users:
                        markup.add(types.KeyboardButton(f"@{user[0]}"))
                    markup.add(types.KeyboardButton("Отмена"))
                    ask_recipient = bot.send_message(message.chat.id, f"Выберите ник пользователя:", reply_markup = markup)
                    bot.register_next_step_handler(ask_recipient, message_to_user_name)
                else:
                    send = True
                    if str(message.text)[0] == '@':
                        user_id = sql("SELECT id FROM users WHERE name = {}".format(f"\"{message.text[1:]}\""))
                        if user_id != None:
                            recipient_ids.append(user_id)
                        else:
                            send = False
                            bot.send_message(message.chat.id, "Пользователь не найден в моей базе данных, убидитесь, что вы правильно написали его ник.",
                                             reply_markup = types.ReplyKeyboardRemove())
                            bot.send_sticker(message.chat.id, get_sticker(["sad", "error"]))
                    elif message.text == recipients[2]:
                        recipient_ids = sql("SELECT id FROM users WHERE access = {}".format(2))
                    elif message.text == recipients[3]:
                        recipient_ids = sql("SELECT id FROM users WHERE access < {}".format(3))
                    if send:
                        ask_text = bot.send_message(message.chat.id, f"Следующее ваше сообщение я отправлю {message.text}. Если передумали - /cancel )",
                                                    reply_markup = types.ReplyKeyboardRemove())
                        bot.register_next_step_handler(ask_text, message_to_user)
            else:
                try:
                    bot.copy_message(sql("SELECT id FROM users WHERE access = {} and name = {}".format(1, f"\"{bot_data('group_title')}\""))[0][0],
                                     message.chat.id, message.message_id)
                    bot.send_message(message.chat.id, "Сообщение отправлено успешно.", reply_markup = types.ReplyKeyboardRemove())
                    bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))
                except:
                    bot.send_message(message.chat.id, "Не получилось отправить сообщение, \
                                                   \n\nвозможно Вы или администратор группы заблокировали бота или ограничили ему доступ.",
                                     reply_markup = types.ReplyKeyboardRemove())
                    bot.send_sticker(message.chat.id, get_sticker(["sad", "error"]))
        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Отменяю отправку. \n(μ_μ) ", reply_markup = types.ReplyKeyboardRemove())

    if str(message.chat.id)[0] != '-':
        update_access = update_user(message)
        if update_access == 2:
            recipient_ids.append(sql("SELECT id FROM users WHERE access = {} and name = {}".format(1, f"\"{bot_data('group_title')}\"")))
            ask_message = bot.send_message(message.chat.id, "Следующее ваше сообщение я отправлю в группу. \
                                                              \nЧтобы отменить - отправте /cancel")
            bot.register_next_step_handler(ask_message, message_to_user)
            bot.send_sticker(message.chat.id, get_sticker(["service"]))
        elif update_access == 3:
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            for recipient in recipients:
                markup.add(types.KeyboardButton(recipient))
            markup.add(types.KeyboardButton("Отмена"))
            ask_recipient = bot.send_message(message.chat.id, "Кому отправить сообщение?", reply_markup = markup)
            bot.register_next_step_handler(ask_recipient, message_to)
            bot.send_sticker(message.chat.id, get_sticker(["service", "lovely"]))
        else:
            bot.send_message(message.chat.id, "Вы не можете пользоваться этой коммандой, потому что вы не имеете к ней доступ. \
                                           \n\nВы не админ и не создатель. \nヽ(~_~)ゝ")
            bot.send_sticker(message.chat.id, get_sticker(["sad"]))
    elif str(message.chat.id)[0] == '-':
        bot.send_message(message.chat.id, f"Вы не можете отправлять сообщения от имени бота в чате группы. \n(＞_＜) \
                                        \n\nЧтобы использовать все доступные комманды напишите в лс боту: @{bot_name}")



@bot.message_handler(commands = ["gradesheet"])
def gradesheet_msg(message):
    lesson = 0
    student_grades = {}
    lessons = sql("SELECT name, max_grade FROM lessons ORDER BY max_grade")[1:]
    for index in lessons:
        student_grades[index[1]] = []

    def create_gradesheet(message):
        if str(message.text).lower() not in cancel:

            def filling_gradesheet(message):
                if str(message.text).lower() not in cancel:

                    def write_mark(message):
                        nonlocal lesson
                        if str(message.text).lower() not in cancel and lesson < len(lessons):
                            if message.text.isnumeric() and lessons[lesson][1] > 0:
                                if int(message.text) <= lessons[lesson][1]:
                                    student_grades[lessons[lesson][1]].append(int(message.text))
                                    student_grade_list.write(f"{lessons[lesson][0]} (макс. балл: {lessons[lesson][1]}): {message.text}\n")
                                    lesson += 1
                                else:
                                    bot.send_message(message.chat.id, f"Вы превысили максимальный балл, так не получится. Попробуйте ещё раз.")
                            elif not message.text.isnumeric() or lessons[lesson][1] == 0:
                                if lessons[lesson][1] > 0:
                                    if message.text != "Оценка не выставлена" and message.text != "Не Атестован":
                                        bot.send_message(message.chat.id, "Вводите оценки только как числа(цифры). Попробуйте ещё раз.")
                                    elif message.text == "Оценка не выставлена":
                                        student_grade_list.write(f"{lessons[lesson][0]} (макс. балл: {lessons[lesson][1]}): -\n")
                                        lesson += 1
                                    elif message.text == "Не Атестован":
                                        student_grade_list.write(f"{lessons[lesson][0]} (макс. балл: {lessons[lesson][1]}): Н.А.\n")
                                        lesson += 1
                                else:
                                    student_grade_list.write(f"{lessons[lesson][0]}: {message.text}\n")
                                    lesson += 1
                            filling_gradesheet(message)
                        elif str(message.text).lower() in cancel:
                            bot.send_message(message.chat.id, "Отменяю составление табеля. \n(´-ω-`) ", reply_markup=types.ReplyKeyboardRemove())
                            student_grade_list.close()
                            os.remove(f"{student_name}.txt")

                    if lesson < len(lessons):
                        if lessons[lesson][1] > 0:
                            mark_question = bot.send_message(message.chat.id, f"Введите оценку по {lessons[lesson][0]} \
                                                                                  \n(максимальная оценка {lessons[lesson][1]}):")
                        else:
                            mark_question = bot.send_message(message.chat.id, f"Введите оценку по {lessons[lesson][0]} \
                                                                                  \n(средний бал этого предмета не считается):")
                        bot.register_next_step_handler(mark_question, write_mark)
                    else:
                        student_grade_list.write(f"\n\n")
                        for max_grade in student_grades.keys():
                            if len(student_grades[max_grade]) == 0:
                                average_value = "Нет ни одной оценки."
                            else:
                                average_value = float("{0:.1f}".format(sum(student_grades[max_grade]) / len(student_grades[max_grade])))
                            student_grade_list.write(f"Средний балл (по {max_grade}-и бальной системе): {average_value}\n")
                        student_grade_list.write(f"\n\n")

                        student_grade_list.write("Обозначения:")
                        student_grade_list.write("\n\"макс. балл\" - максимальная оценка, которая может быть получена;\
                                                  \n\"Н.А.\" - Не атестован(-а). Слишком низкий бал;\
                                                  \n\"-\" - Оценка не выставлена по неизвестной причине.")
                        student_grade_list.close()
                        bot.send_message(message.chat.id, "Составление табеля законченно.", reply_markup=types.ReplyKeyboardRemove())
                        bot.send_document(message.chat.id, open(f"{student_name}.txt", "r"))
                        os.remove(f"{student_name}.txt")

                elif str(message.text).lower() in cancel:
                    bot.send_message(message.chat.id, "Отменяю составление табеля. \n(´-ω-`) ", reply_markup=types.ReplyKeyboardRemove())
                    student_grade_list.close()
                    os.remove(f"{student_name}.txt")

            student_name = message.text
            open(f"{student_name}.txt", "w+", encoding="utf-8").write(f"Оценки {student_name}. \n\n")
            student_grade_list = open(f"{student_name}.txt", "a", encoding="utf-8")

            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            markup.add(types.KeyboardButton("Не Атестован"))
            markup.add(types.KeyboardButton("Оценка не выставлена"))
            markup.add(types.KeyboardButton("Отмена"))
            bot.send_message(message.chat.id, "Приступим к заполнению:", reply_markup = markup)

            filling_gradesheet(message)

        elif str(message.text).lower() in cancel:
            bot.send_message(message.chat.id, "Отменяю составление табеля. \n(´-ω-`) ", reply_markup = types.ReplyKeyboardRemove())


    if str(message.chat.id)[0] != '-':
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(message.chat.id, "Начинаем заполнение табеля по всем предметам!", reply_markup = markup)

        ask_name = bot.send_message(message.chat.id, "Введите имя и фамилию ученика:")
        bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))
        bot.register_next_step_handler(ask_name, create_gradesheet)
    elif str(message.chat.id)[0] == '-':
        bot.send_message(message.chat.id, f"Вы не можете составить табель в чате группы. \n(＞_＜) \
                                        \n\nЧтобы использовать все доступные комманды напишите в лс боту: @{bot_name}")



def help_msg(message):
    if "/start" in message.text:
        bot.send_message(message.chat.id,"Командой /start вы начинаете работу бота. \
                         \nПри выполнении этой команды Вам даётся выбор: \
                         \nДелать ли рассылку о парах в этот чат. \
                         \n(подробнее о рассылке в /FAQ)")
    elif "/rings" in message.text:
        bot.send_message(message.chat.id,"Команда /rings показывает расписание звонков каждого занятия. \
                         \n(часовой пояс - часовой пояс учебного заведения)")
    elif "/today" in message.text:
        bot.send_message(message.chat.id,"Команда /today показывает расписание на сегодня. \
                         \n Если занятий нет, то в сообщении будет сказано что их нет. \
                         \nРасписание редактируется админами и шанс того что оно не правильное мал.")
    elif "/tommorow" in message.text:
        bot.send_message(message.chat.id,"Команда /tommorow показывает расписание занятий на завтра. \
                         \nЕсли завтра выходной, то покажется расписание на ближайший рабочий день. \
                         \nРасписание редактируется админами и шанс того что оно не правильное - мал.")
    elif "/timetable" in message.text:
        bot.send_message(message.chat.id,"Команда /timetable показывает расписание на каждый будний день недели, и показывает какие дни выходные. \
                         \nРасписание редактируется админами и шанс того что оно не правильное - мал.")
    elif "/edit_timetable" in message.text:
        bot.send_message(message.chat.id,"Команда /edit_timetable - для админов, \
                         \nчтоб стать админом вам нужно быть админов в основной группе этого бота. \
                         \nКоманда позволяет редактировать расписание, напоминания и ссылки на занятия. \
                         \nСначала вы отправляете команду боту, потом выбираете что будете редактировать (кнопками): \
                         \nРасписание, Напоминание, Ссылку или Сделать день выходным. Потом если вы выбрали Расписание (мигалки или основное),\
                           то выбираете день недели (кнопками), номер занятия (тоже кнопками, на которых написано название тех занятий,\
                           которые сейчас в расписании) и потом выбираете на какое занятие изменить (тоже кнопками). \
                           Если вы выбирете Напоминание, то так же выбираете день недели, номер занятия и отправляете боту новое напоминание. \
                           (его так же можно удалить при помощи кнопоки Удалить). Напоминание сохраняется одно задание, а после удаляется\
                           Если ты выбираете Ссылку (класса или занятия), то сначала выбор у какого занятия изменить ссылку, \
                           бот отправит вам Предыдущую ссылку. А потом в сообщении вы просто отправляете новую ссылку. ")
    elif "/gradesheet" in message.text:
        bot.send_message(message.chat.id, "Команда /gradesheet - доступна для всех, \
                         \nВы пишете имя ученика, для которого вы будете делать список оценок для журнала (все предметы), потом заполняете оценки.")
    elif "/write" in message.text:
        bot.send_message(message.chat.id,"Команда /write для админов и создателя, \
                         \nчтоб стать админом вам нужно быть админов в основной группе этого бота, \
                         \nа команда позволяет отправить любого типа в группу к которой прикреплен бот, а если ей воспользуется создатель, \
                          то для него будут дополнительные параметры в которых легко разобраться.")
    elif "/faq" in message.text.lower():
        bot.send_message(message.chat.id,"Команда /FAQ - команда, которая показывает часто задаваемые вопросы и ответы на них.")
    elif "/cancel" in message.text:
        bot.send_message(message.chat.id,"Команда /cancel - команда отмены действия. \
                         \nОтменяет любой процес и cкрывает кнопки, если произошла ошибка...")
    else:
        bot.send_message(message.chat.id,"Не такого сообщения я от вас ожидала, поэтому отменяю действие.")
    bot.send_sticker(message.chat.id, get_sticker(["service"]))

def message_to_creator(message):
    if message.text.lower() not in cancel:
        if message.from_user.id == creator_id:
            bot.send_message(message.chat.id, "Вы и есть создатель бота, вам не зачем отправлять себе сообщения. \n(￣_￣)・・・ ")
        else:
            bot.send_message(creator_id, f"Вам пришло сообщение от: @{message.from_user.username} .")
            bot.forward_message(creator_id, message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "Сообщение было доставлено успешно. \nヽ(o＾▽＾o)ノ")
        bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))
    elif message.text.lower() in cancel:
        bot.send_message(message.chat.id, "Хорошо, создателю ничего не отправлем. \n~(>_<~) ")
        bot.send_sticker(message.chat.id, get_sticker(["sad"]))


@bot.message_handler(commands = ["distribution", "help", "hierarchy", "charity", "information", "bots", "support", "updates", "news", "secrets"])
def FAQ_answers(message):
    if message.text == "/distribution":
        bot.send_message(message.chat.id, "Рассылка определяется при вызове команды /start . \
                         \nПо умолчанию рассылка равна \"Не Делать\", поэтому этот шаг можно пропустить. \
                         \nЕсли же Вы выбрали \"Делать\", то за три минуты до начала занятия Вы будете получать сообщение с такой информацией, как\
                         название предстоящего занятия, ссылка на занятие, ссылка на класс занятия, напоминание или заметка к занятию,\
                         а после окончания занятия Вам придет сообщение с названием сдедующего и временем его начала. \
                         \n\nРассылка не рассылает ничего лишнего, только по учебе!")
    elif message.text == "/help":
        ask_help = bot.send_message(message.chat.id, "Пришлите мне команду из списка команд, а я распишу Вам что она делает во всех подробностях. \
                                    \n(список команд находится рядом с полем ввода текста, для отправки нажмите по интересующей вас команде)")
        bot.register_next_step_handler(ask_help, help_msg)
    elif message.text == "/hierarchy":
        bot.send_message(message.chat.id, "Бот должен быть привязан к группе. Иерархия группы, к которой он привязан переносится на бота автоматически. \
                        \n\nУ каждой ступени (обычный пользователь, админ, создатель) есть свои преимущества, как понятно - у создателя их больше всех. \
                        \nСоздателем бота считается человек, который создал группу, а админы - админы группы соответственно. \
                        \nАдмины, как и создатель, могут пользоваться всеми командами. Отличия не большие, \
                        Создатель может пользоваться расширенной версией комманды /write , ему приходят сообщения с команды /support \
                        и доступны секретные команды, которые вы можете посмотреть по команде /secrets .")
    elif message.text == "/charity":
        bot.send_message(message.chat.id, "Вы можете помочь разработчикам несколькими способами: \
                         \n(воспользуйтесь /support для звязи с разработчиками, посмотрите канал, где публикуются обновления от разработчиков @all_dol ) \
                         \n 1) Сообщайте о багах или предлагайте нововведения. \
                         \n 2) Вступить в команду разработчиков и помочь писать код. \
                         \n 3) Помочь деньгами /donation .")
    elif message.text == "/information":
        bot.send_message(message.chat.id, "Информацию о разработке бота вы можете найти на канале: @all_dol . (Закрепленное сообщение) \
                         \nТам так-же публикуются новости и разроботки от создателей этого бота.")
    elif message.text == "/bots":
        bot.send_message(message.chat.id, "Боты для других групп конфиденциальны. \
                         \nЧтобы сделать бота для вашей группы напишите создателям через /support .")
    elif message.text == "/support":
        next_to_creator = bot.send_message(message.chat.id, "Следующее Ваше сообщение будет отправлено создателю бота. \nДля отмены пришлите /cancel.")
        bot.register_next_step_handler(next_to_creator, message_to_creator)
    elif message.text == "/updates":
        bot.send_message(message.chat.id, "Список последних обновлений вы можете найти на канале: @all_dol . \
                         \nТам так-же публикуются новости и разроботки от создателей этого бота.")
    elif message.text == "/news":
        bot.send_message(message.chat.id, "Новостей нет, стараемся завершить бота. \
                         \n\nЕсли интересны новости о ботах и стикерах этого разработчика, то советую подписаться на (официальный) канал: @all_dol .")
    elif message.text == "/secrets":
        bot.send_message(message.chat.id, "У бота есть скрытые функции, которые включены автоматически.\
                        \n\nСписок: \
                        \n - Проверка дней рождений учеников и оповещение, чтоб никто не пропустил их. (команды не требуется) \
                        \n - По просьбе бот даст ссылку на занятие, которое сейчас проходит. (В сообщении должно быть \"Дай ссылку\" \
                        \n - Вы можете получить полную информацию о занятиях, то есть все названия и ссылки. (команда /lessons_info) \
                        \n - Создлатель может узнать полную информацию о боте, в которую входит: Время на сервере, разница во времени, \
                         и состояние рассылки. (команда /bot_info) ")
    bot.send_sticker(message.chat.id, get_sticker(["service"]))


@bot.message_handler(commands = ["donation"])
def donation(message):
    bot.send_message(message.chat.id, str(bot_data("donation_text")) + " \n\nСобрано: " + str(bot_data("donation_amount")) + " денег." +
                     " \nЦель: " + str(bot_data("donation_target")) + " денег.")
    if update_user(message) == 3:
        bot.send_message(message.chat.id, f"/change_donation - изменить текст доната; \n"
                                               f"/donation_amount - добавить или вычесть задоначенные деньги; \n"
                                               f"/donation_target - Изменить целевое количество денег.")


@bot.message_handler(commands = ["change_donation", "donation_amount", "donation_target"])
def donation_actions(message):
    if update_user(message) == 3:
        if message.text == "/change_donation":
            def edit_donation_text(message):
                if message.text.lower() not in cancel:
                    bot_data(set={"donation_text": message.text})
                    bot.send_message(message.chat.id, "Текст доната изменён. \nヽ(o＾▽＾o)ノ")
                    bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))
                elif message.text.lower() in cancel:
                    bot.send_message(message.chat.id, "Хорошо, текст доната не меняю. \n~(>_<~) ")
                    bot.send_sticker(message.chat.id, get_sticker(["sad"]))

            bot.send_message(message.chat.id, "Предыдущий текст к донату был: \n\n" + bot_data("donation_text"))
            change_donation_text = bot.send_message(message.chat.id, "Пришлите новый текст к донату:")
            bot.register_next_step_handler(change_donation_text, edit_donation_text)
        elif message.text == "/donation_amount":
            def edit_donation_amount(message):
                if message.text.lower() not in cancel:
                    try:
                        bot_data(set = {"donation_amount" : bot_data("donation_amount") + int(message.text)})
                        bot.send_message(message.chat.id, "Количество денег теперь " + str(bot_data("donation_amount")) + " денег. \nヽ(o＾▽＾o)ノ")
                        bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))
                    except:
                        bot.send_message(message.chat.id, "Количество денег не изменено, пожалуйста отправляйте числа. \n(个_个) ")
                        bot.send_sticker(message.chat.id, get_sticker(["sad"]))
                elif message.text.lower() in cancel:
                    bot.send_message(message.chat.id, "Количество денег не меняю. \n~(>_<~) ")
                    bot.send_sticker(message.chat.id, get_sticker(["sad"]))

            bot.send_message(message.chat.id, "На данный момент Вам задонатили " + str(bot_data("donation_amount")) + " денег.")
            change_donation_amount = bot.send_message(message.chat.id, "Добавьте или вычтите деньги:")
            bot.register_next_step_handler(change_donation_amount, edit_donation_amount)
        elif message.text == "/donation_target":
            def edit_donation_target(message):
                if message.text.lower() not in cancel:
                    try:
                        bot_data(set = {"donation_target" : int(message.text)})
                        bot.send_message(message.chat.id, "Теперь цель " + str(bot_data("donation_target")) + " денег. \nヽ(o＾▽＾o)ノ")
                        bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))
                    except:
                        bot.send_message(message.chat.id, "Не меняю цель, пожалуйста отправляйте числа. \n(个_个) ")
                        bot.send_sticker(message.chat.id, get_sticker(["sad"]))
                elif message.text.lower() in cancel:
                    bot.send_message(message.chat.id, "Цель не меняю. \n~(>_<~) ")
                    bot.send_sticker(message.chat.id, get_sticker(["sad"]))

            bot.send_message(message.chat.id, "На данный момент Ваша цель " + str(bot_data("donation_target")) + " денег.")
            change_donation_target = bot.send_message(message.chat.id, "Пришлите новую цель:")
            bot.register_next_step_handler(change_donation_target, edit_donation_target)
    else:
        bot.send_message(message.chet.id, "Вы не создатель, вы не можете редактировать что-либо связанное с донатами.")
        bot.send_sticker(message.chat.id, get_sticker(["sad"]))


@bot.message_handler(commands = ["faq", "FAQ"])
def FAQ_msg(message):
    if str(message.chat.id)[0] != '-':
        bot.send_message(message.chat.id, "Часто задаваемые вопросы и некоторая полезная информация:"
                                           "\n\nЧто такое рассылка и зачем мне её включать? \n /distribution \nσ(￣、￣〃) "
                                           "\n\nЕсть описание каждой команды простым языком? \n /help \n(・・ ) ? "
                                           "\n\nКак стать главным или админом в боте? (Как вообще работает иерархия в боте?) \n /hierarchy \n(・_・ヾ "
                                           "\n\nКому писать если у меня забаговал бот? \n /support \n(*μ_μ) "
                                           "\n\nЕсть такие же боты, для других групп? \n /bots \n(↼_↼) "
                                           "\n\nКакие последние обновления (что анонсируют)? \n /updates \n(◎ ◎)ゞ"
                                           "\n\nКак можно помочь разработчикам? \n /charity \n(・・;)ゞ "
                                           "\n\nЧто это за бот и кто его делал? \n /information \n(•ิ_•ิ)? "
                                           "\n\nКакие новости от разработчика, новые стикеры, боты? \n /news \nლ(ಠ_ಠ ლ) "
                                           "\n\nКакие есть секретые или скрытые команды у бота? \n /secrets \n(⊙_⊙) ")
        bot.send_sticker(message.chat.id, get_sticker(["service"]))
    elif str(message.chat.id)[0] == '-':
        bot.send_message(message.chat.id, f"Вы не можете использовать эту команду в чате группы. \
                         \n\n Чтобы использовать эту и прочие комманды напишите в лс боту: @{bot_name} .")



@bot.message_handler(commands = ["lessons_info"])
def lesson_info_msg(message):
    lessons = ["Список всех уроков: "]
    for lesson in sql("SELECT * FROM lessons WHERE rowid > 1"):
        lessons.append(f"{len(lessons)} : {lesson[0]}, \n{' ' * 4}Ссылка на занятие: {lesson[1]}; \n{' ' * 4}Ссылка на класс: {lesson[2]}")
    bot.send_message(message.chat.id, "\n\n".join(lessons))



@bot.message_handler(commands = ["bot_info"])
def bot_info_msg(message):
    if update_user(message) == 3:
        bot.send_message(message.chat.id, f"Время и дата на сервере: {str(datetime.now().date())} {str(datetime.now())[11:16]}.")
        bot.send_message(message.chat.id, f"Установленная разница во времени {time_difference} час(-а), Время у вас: {str(get_datetime())[11:16]}.")
        bot.send_sticker(message.chat.id, get_sticker(["secret"]))
    else:
        bot.send_message(message.chet.id, "Вы не создатель, эта команда вам ни к чему.")
        bot.send_sticker(message.chat.id, get_sticker(["sad"]))



give = ["где", "дай", "кин", "мож"]
@bot.message_handler(content_types = "text")
def text_msg(message):

    if str(message.chat.id)[0] == '-':
        if message.text.lower()[0:3] == "бот":
            if "сылк" in message.text.lower():
                for give_link in give:
                    if give_link in message.text.lower():
                        lesson = lesson_at(get_datetime())
                        if lesson["is_lesson"]:
                            bot.reply_to(message, f"{lesson['name']} {lesson['link']} {lesson['remind']}")
                            bot.send_sticker(message.chat.id, get_sticker(["sad", "study"]))
                        else:
                            bot.reply_to(message, lesson["name"])
                            bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))
                        break
    else:
        if "сылк" in message.text.lower():
            for give_link in give:
                if give_link in message.text.lower():
                    lesson = lesson_at(get_datetime())
                    if lesson["is_lesson"]:
                        bot.reply_to(message, f"{lesson['name']} {lesson['link']} \n\nНапоминание: {lesson['remind']}")
                        bot.send_sticker(message.chat.id, get_sticker(["sad", "study"]))
                    else:
                        bot.reply_to(message, lesson["name"])
                        bot.send_sticker(message.chat.id, get_sticker(["happy", "lovely"]))
                    break
        elif message.text.lower() in cancel:
            bot.reply_to(message, "Отменяю всё возможное и скрываю кнопки, если они открыты.", reply_markup = types.ReplyKeyboardRemove())
            bot.send_sticker(message.chat.id, get_sticker(["error"]))

    update_user(message)


bot.infinity_polling()

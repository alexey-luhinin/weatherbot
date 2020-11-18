import requests
import telebot
from telebot import types
from config import API, TOKEN
from datetime import time
import sqlite3


bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
user_info = {}


def get_weather_by_city(city):
    r = requests.get(
        f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API}\
&units=metric&lang=ru'
    )

    return r.json()

def get_weather_by_location(lat, lon):
    r = requests.get(
        f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}\
&appid={API}&units=metric&lang=ru'
    )

    return r.json()

def parse_weather_json(data):
    try:
        name = data['name']
        country = data['sys']['country']
        description = data['weather'][0]['description']
        main = data['weather'][0]['main']
        wind_speed = data['wind']['speed']
        temp = data['main']['temp']
        temp_min = data['main']['temp_min']
        temp_max = data['main']['temp_max']

        weather_info = {
            'city': name,
            'country': country,
            'description': description,
            'main': main,
            'wind_speed': wind_speed,
            'temp': temp,
            'temp_min': temp_min,
            'temp_max': temp_max,
        }

    except:
        weather_info = None

    return weather_info

def insert_to_db(user_info):
    db = sqlite3.connect('user_info.db')
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS user_info \
(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, city TEXT, time text)")
    c.execute("SELECT * FROM user_info WHERE user_id=%s" % user_info['id'])
    if c.fetchall():
        c.execute("UPDATE user_info SET city='%s', time='%s' WHERE user_id=%s" 
                % (user_info['city'], user_info['time'], user_info['id']))
    else:
        c.execute("INSERT INTO user_info VALUES (null, %s, '%s', '%s')" 
                % (user_info['id'], user_info['city'], user_info['time']))
    db.commit()
    bot.send_message(user_info['id'], 'Готово.')
    db.close()


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 
    "<b>Приветствую Вас!</b>\nВведите любой город, чтобы узнать погоду.\n\n\
Можно определить погоду с помощью геолокации, для этого отправьте боту \
Ваше местоположение.\n\n\
Если хотите чтобы бот присылал Вам погоду каждый день \
введите комманду /set_alarm")


@bot.message_handler(commands=['set_alarm'])
def set_alarm(message):
    msg = bot.send_message(message.chat.id, 
                    'Какой город/населенный пункт хотите мониторить?')
    bot.register_next_step_handler(msg, take_user_city)


@bot.message_handler(content_types=['location'])
@bot.message_handler(content_types=['text'])
def weather_info(message):
    try:
        if message.location:
            data = parse_weather_json(get_weather_by_location(
                                      message.location.latitude, 
                                      message.location.longitude))
        else:
            data = parse_weather_json(get_weather_by_city(message.text))
        output = f'Страна: {data["country"]}\nГород: {data["city"]}\n\
Температура: <b>{data["temp"]}</b>\n\n\
Минимальная температура: {data["temp_min"]}\n\
Максимальная температура: {data["temp_max"]}\n\n\
Скорость ветра: {data["wind_speed"]}\n\n\
{data["description"].capitalize()}'
        bot.send_message(message.chat.id, output)
    except:
        bot.send_message(message.chat.id, 'Ошибка')


def take_user_city(message):
    if parse_weather_json(get_weather_by_city(message.text)):
        user_info['id'] = message.chat.id
        user_info['city'] = message.text
        msg = bot.send_message(message.chat.id, 
        'Выберите время в которое Вам удобно получать оповещение о погоде? \
(формат "hh:mm")')
        bot.register_next_step_handler(msg, take_user_time)
    else:
        bot.send_message(message.chat.id, 'Ошибка')

def take_user_time(message):
    try:
        h, m = [int(n) for n in message.text.split(':')]
        t = time(h, m)
        user_info['time'] = t
        keyboard = types.InlineKeyboardMarkup()
        button_confirm = types.InlineKeyboardButton(text='Подтверждаю', 
                                                    callback_data="yes")
        button_cancel = types.InlineKeyboardButton(text='Отмена', 
                                                    callback_data="no")
        keyboard.add(button_confirm, button_cancel)
        msg = bot.send_message(message.chat.id, f'Подтвердите!\n\n\
Город/Населенный пункт: {user_info["city"]}\n\
Время оповещения: {user_info["time"]}', reply_markup=keyboard)
    except:
        msg = bot.send_message(message.chat.id, 
                               'Формат времени должен быть "hh:mm"')
        bot.register_next_step_handler(msg, set_alarm)


@bot.callback_query_handler(func=lambda call:True)
def controller(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.data == 'yes':
        insert_to_db(user_info)
    elif call.data == 'no':
        bot.send_message(call.message.chat.id, 'Ок!')

if __name__ == "__main__":
    bot.polling(none_stop=True)

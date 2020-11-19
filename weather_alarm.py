import requests
import telebot
from config import API, TOKEN

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


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

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 
    "<b>Приветствую Вас!</b>\nВведите любой город, чтобы узнать погоду.\n\n\
Можно определить погоду с помощью геолокации, для этого отправьте боту \
Ваше местоположение.")


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
        bot.send_message(message.chat.id, 
                        'Я не знаю такого населенного пункта.')


if __name__ == "__main__":
    bot.polling(none_stop=True)

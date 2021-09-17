# imports
import os
import logging
from fastapi import FastAPI as API, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
import datetime
import pymongo
from pymongo import MongoClient
import requests
import json
import telebot
import bs4
import bot.src.markups as markups
import bot.src.youtubebot as youtubebot
from telegram import Location


API_TOKEN = "1395616602:AAEitL36CEX_epUhcJeBFhqE_oc8ZU2NAek" # @GeoBot

# API_TOKEN = '1363386793:AAEq5fcDZEQm0YIV-5Wrl4ku8yU_B_8EABM'  # @pixelray_bot
WEBHOOK_PORT = '8443'
WEBHOOK_HOST = 'bigone.demist.ru'

base_dir = os.path.dirname(__file__)

WEBHOOK_SSL_CERT = os.path.join(base_dir, "webhook_cert.pem")
WEBHOOK_SSL_PRIV = os.path.join(base_dir, "webhook_pkey.pem")

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/bot1/{}/".format(API_TOKEN)

client = MongoClient('mongo', 27017)
db = client['database']
tgbot_users = db['tgbot_users']
tgbot_users_history = db['tgbot_users_history']

tgbot_users.create_index([("chat_id", pymongo.TEXT)], unique=True)
tgbot_users_history.create_index([("chat_id", pymongo.TEXT)])

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)

api = API()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@api.post("/bot1/{token}/")
async def handleWebhook(token, request: Request):
    logging.info("Well done")
    logging.info(token)
    body_dict = await request.json()
    update = telebot.types.Update.de_json(body_dict)
    bot.process_new_updates([update])
    return

@api.post("/bot2/{token}/")
async def handleWebhook(token, request: Request):
    logging.info("Well done")
    logging.info(token)
    body_dict = await request.json()
    update = telebot.types.Update.de_json(body_dict)
    youtubebot.bot.process_new_updates([update])
    return

def save_user_action_to_db(chat_id, **kwargs):
    action_data = {"chat_id": chat_id, "date": datetime.datetime.utcnow()}
    action_data.update(kwargs)
    tgbot_users_history.insert_one(action_data)


from geopy.geocoders import Nominatim
import pandas as pd
geocoder = Nominatim(user_agent='geovideo')
def convert(geo_names):
    coordinates = []
    for name in geo_names:
        location = geocoder.geocode(name)
        coordinates.append([location.latitude, location.longitude])
    info = pd.DataFrame(coordinates, columns=['latitude', 'longitude'])
    return "latitude and longitude: " + str(coordinates[0])


def get_latitude(geo_name):
    return geocoder.geocode(geo_name).latitude

def get_longitude(geo_name):
    return geocoder.geocode(geo_name).longitude


@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    chat_id = message.chat.id
    username = message.from_user.username
    save_user_action_to_db(chat_id, action="start_handler")
    user_data = {
        "chat_id": chat_id,
        "username": username
    }
    logging.info(f"username={str(username)}")
    try:
        tgbot_users.insert_one(user_data)
    except:
        logging.info("user already exists")
    msg = bot.send_message(
        chat_id, 'Привет)\nСколько видео по теме ты хочешь искать?', reply_markup=markups.maxres_markup)
    bot.register_next_step_handler(msg, askMaxResults)


def askMaxResults(message):
    chat_id = message.chat.id
    text = message.text
    if text.isdigit():
        tgbot_users.update_one({"chat_id": chat_id}, {
                               "$set": {"amount": text}},  upsert=False)
        msg = bot.send_message(
            chat_id, f'Отлично. Будем искать {text} лучших видео по теме:')
        bot.register_next_step_handler(msg, askSource)
    else:
        msg = bot.send_message(
            chat_id, 'Введите, пожалуйста натуральное число')
        bot.register_next_step_handler(msg, askMaxResults)
        return


def askSource(message):
    chat_id = message.chat.id
    text = message.text.lower()
    tgbot_users.update_one({"chat_id": chat_id}, {
        "$set": {"topic": text}},  upsert=False)

    user = tgbot_users.find_one({"chat_id": chat_id})
    logging.info(f"user={str(user)}")
    response = requests.get("http://web:8000/youtube/video/urlsbyprompt",
                            params={"prompt": text, "maxResult": user['amount']})
    video_urls = json.loads(response.text)

    for url in video_urls:
        bot.send_message(chat_id, url)

    msg = bot.send_message(
        chat_id, 'Оцените релевантность видео', reply_markup=markups.rating_markup)
    bot.register_next_step_handler(msg, nextActions)


def nextActions(message):
    chat_id = message.chat.id
    msg = bot.send_message(
        chat_id, 'Выберете дальнейшие действия', reply_markup=markups.video_markup)
    bot.register_next_step_handler(message, nextVideo)


def nextVideo(message):
    chat_id = message.chat.id
    user = tgbot_users.find_one({"chat_id": chat_id})
    if message.text == 'Показать еще 3 видео':
        new_amount = int(user['amount']) + 3
        tgbot_users.update_one({"chat_id": chat_id}, {
            "$set": {"amount": new_amount}},  upsert=False)

        response = requests.get("http://web:8000/youtube/video/urlsbyprompt",
                                params={"prompt": user['topic'], "maxResult": new_amount})
        video_urls = json.loads(response.text)
        for url in video_urls[::-1][0:3]:
            bot.send_message(chat_id, url)

        msg = bot.send_message(
            chat_id, 'Выберете дальнейшие действия', reply_markup=markups.video_markup)
        bot.register_next_step_handler(msg, nextVideo)
    if message.text == 'Начать заново':
        msg = bot.send_message(
            chat_id, 'Напишите /go')
        bot.register_next_step_handler(msg, start_handler)

    if message.text == 'Показать геолокацию места':
        bot.send_message(chat_id, convert([user['topic']]))
        bot.send_location(chat_id, get_latitude(user['topic']), get_longitude(user['topic']))
        msg = bot.send_message(
            chat_id, 'Выберете дальнейшие действия', reply_markup=markups.video_markup)
        bot.register_next_step_handler(msg, nextVideo)



bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

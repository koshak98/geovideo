# imports
# -*- coding: UTF-8 -*-
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
from telebot import types
from telegram import Location

lang_dict = {
    'ru': {
        'views': "просмотров",
        'comments': "комментариев",
        'video_comments': "Комментарии",
        'months': {
            '1': "янв.",
            '2': "фев.",
            '3': "марта",
            '4': "апр.",
            '5': "мая",
            '6': "июня",
            '7': "июля",
            '8': "авг.",
            '9': "cент.",
            '10': "окт.",
            '11': "ноября",
            '12': "дек."
        },
        'topic': "Напиши название видео или тему, чтобы я смог тебе помочь",
        'next_action': "Выберите дальнейшие действия",
        'more_video': "Еще видео",
        'new_search': "Новый поиск",
        'change_lang': "🇷🇺/🇬🇧 Сменить язык",
        'choose_lang': "Выберите язык / Choose language",
        'lang': {"🇷🇺 Русский", "🇬🇧 English"}
    }, 
    'en': {
        'views': "views",
        'comments': "comments",
        'video_comments': "Comments",
        'months': {
            '1': "January",
            '2': "February",
            '3': "March",
            '4': "April",
            '5': "May",
            '6': "June",
            '7': "July",
            '8': "August",
            '9': "September",
            '10': "October",
            '11': "November",
            '12': "December"
            },
        'topic': "Write a video title of topic so I can help you",
        'next_action': "Choose the next action",
        'more_video': "More videos",
        'new_search': "New search",
        'change_lang': "🇬🇧/🇷🇺 Change language",
        },
        'choose_lang': "Choose language / Выберите язык",
        'lang': {"🇷🇺 Русский", "🇬🇧 English"}
    };

#TODO: filter urls in description 

API_TOKEN = '1285861906:AAFEyLUp8iPeGsdxr4M3jNWLfxSRGHBqed0' # @fstvideosearch_bot

WEBHOOK_PORT = '8443'
WEBHOOK_HOST = 'bigone.demist.ru'

base_dir = os.path.dirname(__file__)

WEBHOOK_SSL_CERT = os.path.join(base_dir, "webhook_cert.pem")
WEBHOOK_SSL_PRIV = os.path.join(base_dir, "webhook_pkey.pem")

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/bot2/{}/".format(API_TOKEN)

client = MongoClient('mongo', 27017)
db = client['database']
youtubebot_users = db['youtubebot_users']
youtubebot_users_history = db['youtubebot_users_history']

youtubebot_users.create_index([("chat_id", pymongo.TEXT)], unique=True)
youtubebot_users_history.create_index([("chat_id", pymongo.TEXT)])

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)

def save_user_action_to_db(chat_id, **kwargs):
    action_data = {"chat_id": chat_id, "date": datetime.datetime.utcnow()}
    action_data.update(kwargs)
    youtubebot_users_history.insert_one(action_data)

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
        youtubebot_users.insert_one(user_data)
        msg = bot.send_message(
                chat_id, lang_dict['choose_lang'],
                reply_markup=markups.language_choice_markup)
        bot.register_next_step_handler(msg, changeLanguage)
    except:
        msg = bot.send_message(chat_id, lang_dict['ru']['topic'])
        bot.register_next_step_handler(msg, showVideos)
        logging.info("user already exists")


def showVideos(message):
    chat_id = message.chat.id
    text = message.text.lower()
    youtubebot_users.update_one({"chat_id": chat_id}, {
        "$set": {"topic": text}},  upsert=False)
    youtubebot_users.update_one({"chat_id": chat_id}, {
                               "$set": {"amount": 3}},  upsert=False)
    user = youtubebot_users.find_one({"chat_id": chat_id})
    lang = user['language']
    save_user_action_to_db(chat_id, action="show_videos")
    response = requests.get("http://web:8000/youtube/video/infosbyprompt",
                            params={"prompt": text, "maxResult": user['amount']})
    videos = json.loads(response.text)
    for video in videos:
        videoInfo(chat_id, video, lang)

    msg = bot.send_message(
        chat_id, lang_dict[lang]['next_action'],
        reply_markup=markups.get_youtube_search_markup(lang, lang_dict))
    bot.register_next_step_handler(msg, nextAction)

def nextAction(message):
    chat_id = message.chat.id
    user = youtubebot_users.find_one({"chat_id": chat_id})
    lang = user['language']
    if message.text == lang_dict[lang]['more_video']:
        save_user_action_to_db(chat_id, action="more_video")
        new_amount = int(user['amount']) + 3
        youtubebot_users.update_one({"chat_id": chat_id}, {
            "$set": {"amount": new_amount}},  upsert=False)

        response = requests.get("http://web:8000/youtube/video/infosbyprompt",
                                params={"prompt": user['topic'], "maxResult": new_amount})
        videos = json.loads(response.text)
        for video in videos[::-1][0:3]:
            videoInfo(chat_id, video, lang)

        msg = bot.send_message(
            chat_id, lang_dict[lang]['next_action'],
            reply_markup=markups.get_youtube_search_markup(lang, lang_dict))
        bot.register_next_step_handler(msg, nextAction)

    if message.text == lang_dict[lang]['new_search']:
        save_user_action_to_db(chat_id, action="new_search")
        msg = bot.send_message(
            chat_id, lang_dict[lang]['topic'])
        bot.register_next_step_handler(msg, showVideos)

    if message.text == lang_dict[lang]['change_lang']:
        save_user_action_to_db(chat_id, action="change_lang")
        msg = bot.send_message(
            chat_id, lang_dict['choose_lang'],
            reply_markup=markups.language_choice_markup)
        bot.register_next_step_handler(msg, changeLanguage)

def videoInfo(chat_id, video, lang):
    date_time_obj = datetime.datetime.strptime(video['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
    date_of_upload = "{} {} {}".format(str(date_time_obj.day), lang_dict[lang]['months'][str(date_time_obj.month)], str(date_time_obj.year))
    
    # url button
    comments_keyboard = types.InlineKeyboardMarkup()
    comm_url_button = types.InlineKeyboardButton(text=lang_dict[lang]['video_comments'], url=video['url'])
    comments_keyboard.add(comm_url_button)
    # url button

    bot.send_message(chat_id, video['url'], reply_markup=comments_keyboard)

    bot.send_message(chat_id,
    "{} {}      {}     👍 {}  👎 {}".format(str(video['statistics']['viewCount']),
    lang_dict[lang]['views'], date_of_upload, str(video['statistics']['likeCount']), 
    str(video['statistics']['dislikeCount'])))

    


def changeLanguage(message):
    chat_id = message.chat.id
    if message.text == "🇷🇺 Русский":
        save_user_action_to_db(chat_id, action="choose_lang_ru")
        youtubebot_users.update_one({"chat_id": chat_id}, {
                            "$set": {"language": "ru"}},  upsert=False)
        msg = bot.send_message(
            chat_id, 'Прекрасно, выбран русский язык.'
        )
    elif message.text == "🇬🇧 English":
        save_user_action_to_db(chat_id, action="choose_lang_en")
        youtubebot_users.update_one({"chat_id": chat_id}, {
                            "$set": {"language": "en"}},  upsert=False)
        msg = bot.send_message(
            chat_id, 'Nice, the English language is chosen.'
        )
    user = youtubebot_users.find_one({"chat_id": chat_id})
    lang = user['language']
    logging.info(f"lang={str(lang)}")
    msg = bot.send_message(chat_id, lang_dict[str(lang)]['topic'])
    bot.register_next_step_handler(msg, showVideos)
    
bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

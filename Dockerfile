FROM python:3.8.3-buster

RUN python3.8 -m pip install aiotg fastapi uvicorn requests==2.7.0 pyTelegramBotAPI bs4 google-api-python-client python-telegram-bot pymongo pandas geopy

RUN mkdir /src

COPY . /src

WORKDIR /src

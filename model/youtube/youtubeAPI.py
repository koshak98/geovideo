# Обёртка для YouTube Data API, позволяющая проще получать необходимые для проекта данные
#
# ИНТЕРФЕЙС:
#   getVideoInfoByPrompt(prompt, maxResults=20) - возвращает generator expression из объектов
#       {
#           "Id": Id видео                               # string
#           "title": название                            # string
#           "description": описание                      # string
#           "commentThreads": треды комментариев         # generator expression of strings
#           "statistics": statistics                     # dict
#       }
#     по запросу prompt к поисковой строке
#
#   getUrlByVideoId(videoId) - возвращает URL по Id видео
#
#
# ПРИМЕЧАНИЕ:
#   если лимит запросов превышен, то можно попробовать поменять ключ API на один из запасных в коде функции connectToYoutubeApi()
#
#
# /TODO:
#   разобраться с квотами
#   разобраться с обёрткой для страниц

import io
import os
import json
import logging

from typing import Optional, Dict, List, Tuple, Any

# import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from googleapiclient.http import MediaIoBaseDownload

# *****************************************************************************************************
# первоначальное подключение к raw API
def connectToYoutubeApi():
    base_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(base_dir, "config.json")

    config_data = {}
    with open(config_file_path) as json_file:
        config_data = json.load(json_file)

    return googleapiclient.discovery.build(
        config_data['youtube_api_service_name'],
        config_data['youtube_api_version'],
        developerKey=config_data['api_key'])                        # основной ключ API
                                                                    # ниже ключи на случай, если лимит основного превышен
        # developerKey='AIzaSyANAnLU2iloDqogIAfskp1b3vDxocC0dgQ')


# Объект youtube идеологически является синглтоном
youtube = connectToYoutubeApi()
# *****************************************************************************************************

# ***** lets use OOP style, example of method and class definition here ***

# class YouTubeConnectApi:   
#     def __init__(self, config_file: str = "config.json"):
#         config_data = {}
#         with open(config_file) as json_file:
#             config_data = json.load(json_file)

#         self.youtube = googleapiclient.discovery.build(
#             config_data['youtube_api_service_name'],
#             config_data['youtube_api_version'],
#             developerKey=config_data['api_key'])                        # основной ключ API
#         # ниже ключи на случай, если лимит основного превышен
#         # developerKey='AIzaSyANAnLU2iloDqogIAfskp1b3vDxocC0dgQ')

#     # возвращает Id русских субтитров
#     def getRuCaptionsIdByVideoId(self, videoId: int) -> Optional[int]:
#         request = self.youtube.captions().list(
#             videoId=videoId,
#             part="snippet"
#         ).execute()

#         for caption in request['items']:
#             if caption['snippet']['language'] == "ru":
#                 return caption['id']

#         return None


# *****************************************************************************************************
# РАБОТА С СУБТИТРАМИ


# записывает субтитры с Id==captionsId в outputFile
# у скачивания субтитров очень большая quota cost,
# так что пока я не проверял метод
def getCaptionsTextById(captionsId, outputFile):
    request = youtube.captions().download(
        id=captionsId
    )
    fh = io.FileIO(outputFile, "wb")

    download = MediaIoBaseDownload(fh, request)
    complete = False
    while not complete:
        _, complete = download.next_chunk()
# *****************************************************************************************************


# *****************************************************************************************************
# вспомогательный класс для информации по видео
# содержит Id, заголовок, описание, ветки комментариев и статистику (просмотры, лайки и т.д.)
class videoInfo:
    def __init__(self, Id, title, description, commentThreads, statistics, publishedAt, url):
        self.Id = Id                            # string
        self.title = title                      # string
        self.description = description          # string
        self.commentThreads = commentThreads    # generator expression of strings
        self.statistics = statistics            # dict
        self.publishedAt = publishedAt 
        self.url = url 

    # для дебага
    def __str__(self):
        comments = ''
        for commentThread in self.commentThreads:
            for comment in commentThread:
                comments += '\n  * ' + comment
        return 'Id: {0}\nTitle: {1}\nDescription: {2}\nComments: {3}\nStatistics: {4}'.format(
            self.Id, self.title, self.description, comments, self.statistics
        )
    def to_dict(self):
        return {
            "title": self.title,
            "id": self.Id,
            "description": self.description,
            "statistics": self.statistics,
            "url": self.url,
            "publishedAt": self.publishedAt
        }
# *****************************************************************************************************


# *****************************************************************************************************
# ОСНОВНАЯ РАБОТА С НУЖНОЙ ИНФОРМАЦИЕЙ

# обёртка для прохода по всем страницам результата поискового запроса
# пока что возвращает только элементы на первой странице,
# число которых ограничено maxResults (аргумент запроса; от 1 до 100, default=20)
# /TODO понять, что делать с другими страницами - возможно стоит написать generator expression, переходящий от одной к другой
# полезно:
#   информация по методу поиска - https://developers.google.com/youtube/v3/docs/search
#   про страницы: https://developers.google.com/youtube/v3/guides/implementation/pagination
def paginationWrapper(paginationObject):
    return paginationObject['items']

# обёртка для прохода по ветке комментариев (только если запрос на snippet) - возврашает список словарей-комментариев
# пока что возвращает только первый комментарий
# текст содержится в comment['snippet']['textDisplay']
# /TODO научиться возвращать вместе с replies
# /TODO понять, полезен ли параметр comment['viewerRating']


def commentThreadWrapper(commentThreadObject):
    # список, т.к. в в треде несколько комментариев
    return [commentThreadObject['snippet']['topLevelComment']]

# аналогично, но возвращается сразу список текстов комментариев


def commentThreadWrapperToText(commentThreadObject):
    topLevelComment = commentThreadObject['snippet']['topLevelComment']
    return [topLevelComment['snippet']['textDisplay']]

# обёртка для прохода по всем комментариям, возвращаемым youtube.commentThreads().list()
# пока возвращает только первую страницу результатов
# /TODO понять, нужно ли получать другие страницы - возможно стоит написать generator expression


def commentThreadListWrapper(commentThreadListObject):
    return commentThreadListObject['items']

# функция возвращает все комменатарии к видео в виде generator expression из словарей-комментариев
# примечание: насколько я понял, нельзя получать треды сразу к нескольким видео,
#             поэтому использовать квоту лучше,
#             чем получая все треды по одному видео, не выйдет


def getCommentsByVideoId(videoId, maxResults=20):
    request = youtube.commentThreads().list(part="snippet,replies",
                                            videoId=videoId,
                                            maxResults=maxResults).execute(),
    commentThreadList = commentThreadListWrapper(request)
    for commentThread in commentThreadList:
        yield commentThreadWrapper(commentThread)

# аналогично, но возвращает тексты


def getCommentsTextByVideoId(videoId, maxResults=20):
    request = youtube.commentThreads().list(part="snippet,replies",
                                            videoId=videoId,
                                            maxResults=maxResults).execute()
    commentThreadList = commentThreadListWrapper(request)
    for commentThread in commentThreadList:
        yield commentThreadWrapperToText(commentThread)


# возвращает статистику видео (просмотры, лайки и т.д.) в виде generator expression из словарей-статистик
# при необходимости также можно возвращать длину видео
#   (video['contentDetails']['duration'] -
#    для этого необходимо добавить part+='contentDetails' и ещё кое-что)
# idList имеет формат "id1,id2,..."
def getStatisticsByVideoIds(idList):
    request = youtube.videos().list(
        part="statistics",
        id=idList).execute()
    for info in request['items']:
        yield info['statistics']


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ФУНКЦИИ, ПОЛУЧАЮЩИЕ ИНФОРМАЦИЮ ПО ЗАПРОСУ В ПОИСКОВОЙ СТРОКЕ (запрос==prompt)

# про видео из интересующих параметров возвращает название и описание
# (video['snippet']['title'] and video['snippet']['description'])
# метод youtube.search() вообще не возвращает комментарии и статистику
def searchByPrompt(prompt, *, type='video', maxResults=20):
    request = youtube.search().list(
        part='snippet',
        type=type,
        maxResults=maxResults,
        q=prompt
    ).execute()

    return paginationWrapper(request)


# возвращает generator expression из объектов videoInfo с Id, названием, описанием, тредами комментариев и статистикой
def getVideoInfoByPrompt(prompt, maxResults=20):
    videos = searchByPrompt(prompt, maxResults=maxResults)

    logging.info(f"videos={str(videos)}")
    # /TODO понять, как работают квоты
    # если квота действует на количество поисковых запросов,
    # а не на количество возвращённых результатов,
    # то сбор статистики сразу по всем видео уменьшит затраты
    idListAsString = ''
    for video in videos:
        idListAsString += video['id']['videoId'] + ','
    # убираем последнюю запятую
    idListAsString = idListAsString[:-1]
    statisticsList = getStatisticsByVideoIds(idListAsString)

    for video in videos:
        Id = video['id']['videoId']
        title = video['snippet']['title']
        description = video['snippet']['description']
        publishedAt = video['snippet']['publishedAt']
        url = getUrlByVideoId(Id)

        commentThreads = getCommentsTextByVideoId(Id)
        statistics = next(statisticsList)

        yield videoInfo(Id,
                        title,
                        description,
                        commentThreads,
                        statistics,
                        publishedAt,
                        url)
# *****************************************************************************************************


# *****************************************************************************************************
# НЕ ПРИГОДИВШИЕСЯ ПОКА ЧТО, НО УЖЕ НАПИСАННЫЕ ФУНКЦИИ

# перевод json строки в dict
def decode(json_string):
    return json.JSONDecoder().decode(json_string)

# получение URL видео по его Id


def getUrlByVideoId(videoId):
    return f'https://www.youtube.com/watch?v={videoId}'

# возвращает Ids видео по запросу


def getVideoIdsByPrompt(prompt, maxResults=20):
    videos = searchByPrompt(prompt, maxResults=maxResults)
    return [video['id']['videoId'] for video in videos]

# id_list приходит как строка в формате "id1,id2,id3,..."


def getVideosById(id_list):
    request = youtube.videos().list(
        part='snippet',
        id=id_list
    ).execute()

    return request['items']

# id_list приходит как строка в формате "id1,id2,id3,..."


def getCommentsById(id_list):
    request = youtube.comments().list(
        part='snippet',
        id=id_list
    ).execute()

    return request['items']

# comment должен содержать snippet, иначе функция не работает
# (*если не содержит snippet, то точно содержит id)


def getCommentText(comment):
    return comment['snippet']['textDisplay']
# *****************************************************************************************************


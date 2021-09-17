import os
import logging

import pymongo
from pymongo import MongoClient
from fastapi import FastAPI as API
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse

from model.youtube.youtubeAPI import getVideoInfoByPrompt, getUrlByVideoId

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

api = API()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

client = MongoClient('mongo', 27017)
db = client['test-database']
collection = db['test-collection']

# ******* uncomment for use with class *******
# don't forget to import YouTubeConnectApi

# base_dir = os.path.dirname(__file__)
# config_file_path = os.path.join(base_dir, "../configs/youtube-config.json")
# youTubeApi = YouTubeConnectApi(config_file_path)


@api.get("/youtube/video/urlsbyprompt")
def getVideoUrlsByPrompt(prompt: str, maxResult: int):
    videosInfo = getVideoInfoByPrompt(prompt, maxResult)
    logging.info(f"videosInfo={str(videosInfo)}")
    result = map(lambda video: getUrlByVideoId(video.Id), videosInfo)
    return JSONResponse(list(result))


@api.get("/youtube/video/infosbyprompt")
def getVideosInfoByPrompt(prompt: str, maxResult: int):
    videosInfo = getVideoInfoByPrompt(prompt, maxResult)
    logging.info(f"videosInfo={str(videosInfo)}")
    # return JSONResponse(list(videosInfo))
    return JSONResponse(list(map(lambda x: x.to_dict(), videosInfo)))
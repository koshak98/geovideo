**Док по модулю [youtubeAPI](https://github.com/demist/geovideo/tree/youtube/model/youtube)**  
**Для использования необходимо импортировать youtubeAPI.py**  
**Описание интерфейса пока находится внутри .py файла**  

*Используем Python*  
*На данный момент использование OAuth не предполагается - доступ осуществляется засчёт ключа API*
*Для использования модуля*

# Необходимая информация по API
Для использования API необходим проект в Google APIs.  
Наш проект называется **geovideo-1c-test** и связан с аккаунтом *geovideo.1c.test@gmail.com* (предназначен для тестирования; пароль: *geovideo_1c_test*).



# Работа с API
[Google APIs Client Library for Python documentation](https://github.com/googleapis/google-api-python-client)  
[YouTube Data API PyDoc documentation](https://developers.google.com/resources/api-libraries/documentation/youtube/v3/python/latest/)  
[YouTube Data API reference documentation](https://developers.google.com/youtube/v3/docs)  
[Введение в YouTube Data API](https://developers.google.com/youtube/v3/getting-started) - полезно потыкаться и позапускать примеры в нужных нам разделах  

[Краткий гайд по подключению Google API](https://github.com/googleapis/google-api-python-client/blob/master/docs/start.md)  
[Краткий гайд по Youtube Data API в Python](https://developers.google.com/youtube/v3/quickstart/python)  

## Выдержки:  
*Подключение API*  
- Python 2.7 or Python 3.5+
- pip installation:  
  `pip install --upgrade google-api-python-client`
- Anaconda installation:  
  `conda install -c conda-forge google-api-python-client`
- подключение к API (параметры лежат в [config.json](https://github.com/demist/geovideo/blob/youtube/model/youtube/config.json))  
  ```
  youtube = googleapiclient.discovery.build(
        config_data['youtube_api_service_name'],
        config_data['youtube_api_version'],
        developerKey=config_data['youtube_api_key'])
  ```

*Структура объектов, используемых в коде модуля (однозначно нерелевантные поля убраны)*
- словари-треды комментариев ([доп. информация](https://developers.google.com/youtube/v3/docs/commentThreads))
  ```
  {
    "kind": "youtube#commentThread",
    "etag": etag,
    "id": string,
    "snippet": {
      "channelId": string,
      "videoId": string,
      "topLevelComment": comments Resource,
      "canReply": boolean,
      "totalReplyCount": unsigned integer,
      "isPublic": boolean
    },
    "replies": {
      "comments": [
        comments Resource
      ]
    }
  }
  ```
- словари-комментарии ([доп. информация](https://developers.google.com/youtube/v3/docs/comments))
  ```
  {
    "kind": "youtube#comment",
    "etag": etag,
    "id": string,
    "snippet": {
      "authorDisplayName": string,
      "authorProfileImageUrl": string,
      "authorChannelUrl": string,
      "authorChannelId": {
        "value": string
      },
      "channelId": string,
      "videoId": string,
      "textDisplay": string,
      "textOriginal": string,
      "parentId": string,
      "canRate": boolean,
      "viewerRating": string,
      "likeCount": unsigned integer,
      "moderationStatus": string,
      "publishedAt": datetime,
      "updatedAt": datetime
    }
  }
  ```
- словари-видео ([доп. информация](https://developers.google.com/youtube/v3/docs/videos))
  ```
  {
    "kind": "youtube#video",
    "etag": etag,
    "id": string,
    "snippet": {
      "publishedAt": datetime,
      "channelId": string,
      "title": string,
      "description": string,
      "tags": [
        string
      ],
      "categoryId": string,
      "liveBroadcastContent": string,
      "defaultLanguage": string,
      "localized": {
        "title": string,
        "description": string
      },
      "defaultAudioLanguage": string
    },
    "contentDetails": {
      "duration": string,
      },
    "statistics": {
      "viewCount": unsigned long,
      "likeCount": unsigned long,
      "dislikeCount": unsigned long,
      "favoriteCount": unsigned long,
      "commentCount": unsigned long
    },
    "topicDetails": {
      "topicIds": [
        string
      ],
      "relevantTopicIds": [
        string
      ],
      "topicCategories": [
        string
      ]
    }
  }
  ```

# TODO
- разобраться, насколько важны квоты на операции  
- разобраться с переходами между страницами в поисковых запросах  
  (как вариант - обернуть в generator expression; сам механизм переключения можно извлечь здесь - https://stackoverflow.com/questions/14173428/how-to-change-page-results-with-youtube-data-api-v3)  
- учесть возможность комментариев не на русском  
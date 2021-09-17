from telebot import types

start_markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
start_markup_btn1 = types.KeyboardButton('/start')
start_markup.add(start_markup_btn1)

maxres_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
maxres_markup_btn1 = types.KeyboardButton('1')
maxres_markup_btn2 = types.KeyboardButton('3')
maxres_markup_btn3 = types.KeyboardButton('5')
maxres_markup_btn4 = types.KeyboardButton('10')
maxres_markup_btn5 = types.KeyboardButton('15')
maxres_markup.add(maxres_markup_btn1, maxres_markup_btn2,
                  maxres_markup_btn3, maxres_markup_btn4, maxres_markup_btn5)

video_markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
video_markup_btn1 = types.KeyboardButton('Показать еще 3 видео')
video_markup_btn2 = types.KeyboardButton('Показать геолокацию места')
video_markup_btn3 = types.KeyboardButton('Начать заново')
video_markup.add(video_markup_btn1, video_markup_btn2, video_markup_btn3)

rating_markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
rating_markup_btn1 = types.KeyboardButton('Плохо')
rating_markup_btn2 = types.KeyboardButton('Нормально')
rating_markup_btn3 = types.KeyboardButton('Хорошо')
rating_markup_btn4 = types.KeyboardButton('Отлично')
rating_markup.row(rating_markup_btn1, rating_markup_btn2)
rating_markup.row(rating_markup_btn3, rating_markup_btn4)

amount_markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
amount_markup_btn1 = types.KeyboardButton('1')
amount_markup_btn2 = types.KeyboardButton('3')
amount_markup_btn3 = types.KeyboardButton('5')
amount_markup.add(amount_markup_btn1, amount_markup_btn2, amount_markup_btn3)


def get_youtube_search_markup(lang, lang_dict): 

  youtube_search_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True,
                                                  one_time_keyboard=True)
  youtube_search_markup_btn1 = types.KeyboardButton(lang_dict[lang]['more_video'])
  youtube_search_markup_btn2 = types.KeyboardButton(lang_dict[lang]['new_search'])
  youtube_search_markup_btn3 = types.KeyboardButton(lang_dict[lang]['change_lang'])
  youtube_search_markup.add(youtube_search_markup_btn1, youtube_search_markup_btn2,
                          youtube_search_markup_btn3)
  return youtube_search_markup

language_choice_markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True,
                                                   one_time_keyboard=True,
                                                   selective=True) 
language_choice_markup_bth1 = types.KeyboardButton('🇷🇺 Русский')
language_choice_markup_btn2 = types.KeyboardButton('🇬🇧 English')
language_choice_markup.add(language_choice_markup_bth1,
                           language_choice_markup_btn2)

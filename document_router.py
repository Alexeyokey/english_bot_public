from aiogram import Router, F, types
import re
import asyncio
import langid
from Constants import ENGLISH_PUNCTUATION
from random import choice, randint
from autocorrect import Speller
from api.yandex_api import translate
from db.database import User, Word, UserToWords
import os
from loader import bot


router = Router()


lang = "en"
spell = Speller(lang=lang)

@router.message(F.document)
async def doc_handler(message: types.Message):
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_name = "user_dict.txt"
    await bot.download_file(file_path, "downloadable_files/" + file_name)
    user_in = message.from_user.id
    with open("downloadable_files/" + file_name, "r") as file:
        text = file.read()
        for i in ENGLISH_PUNCTUATION:
            text = text.replace(i, '')
        words = [word.rstrip() for word in text.split()]
    wrong_spelled_words = []
    error_flag = False
    for word in words:
        try:
            user_words_ids = UserToWords.select(UserToWords.word_id).where(UserToWords.user_id == message.from_user.id)
            scr = langid.classify(word)[0]
            word_spelled = spell(word)
            if scr != 'ru':
                word_spelled = spell(word)
                if word_spelled != word:
                    wrong_spelled_words.append((word, word_spelled))
                    continue
                ans = await translate(word, target_language='ru')
            else:
                word_spelled = spell(word)
                if word_spelled != word:
                    wrong_spelled_words.append((word, word_spelled))
                    continue
                ans = await translate(word, target_language='en')
            if scr != 'ru':
                if Word.select().where((Word.id.in_(user_words_ids)) & (Word.en_word == word)).exists():
                    continue
                translation = await translate(word, target_language='ru')
                new_user_word = Word.create(en_word=word, ru_word=translation)
                new_user_word.save() 
                connection = UserToWords.create(user_id=user_in, word_id=new_user_word)
                connection.save()
            else:
                if Word.select().where((Word.id.in_(user_words_ids)) & (Word.ru_word == word)).exists():
                    continue
                translation = await translate(word, target_language='en')
                new_user_word = Word.create(en_word=translation, ru_word=word)
                new_user_word.save() 
                connection = UserToWords.create(user_id=user_in, word_id=new_user_word)
                connection.save()
        except Exception as e:
            print(e)
            error_flag = True
            pass
    if not error_flag:
        await message.answer('Новые слова добавлены в словарь')
    else:
        await message.answer('Что-то пошло не так')
    if wrong_spelled_words:
        text = "Посмотрите на слова, которые могли быть написаны неверно:"
        for word in wrong_spelled_words:
            text += '\n' + word[0] + " - возможно вы имели ввиду: "  + word[1]
        await message.answer(text)
    os.remove("downloadable_files/" + file_name)
from aiogram import Router, F, types
import logging
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from api.tokens_api import API_TOKEN, YANDEX_FOLDER_ID
import langid
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from random import choice, randint, choices
from autocorrect import Speller
from db.database import User, Word, UserToWords
import os
from Constants import HELP_MESSAGE
from learning_router import learn_main
from api.yandex_api import translate, gpt_request

router = Router()

lang = "en"
spell = Speller(lang=lang)

class UserWriting(StatesGroup):
    tranlator_mode = State()
    add_words = State()
    ai_conversation = State()
    delete_words = State()
    learning = State()

@router.message(Command("tranlator_mode"))
async def user_translate(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != UserWriting.tranlator_mode:
        await state.set_state(UserWriting.tranlator_mode)
        await message.answer(f"Ваш режим переключен на переводчик\nПишите мне слова, а я их переведу")
    else:
        await message.answer(f"Вы и так находитесь в режиме переводчика")


@router.message(Command("add_words"))
async def add_words(message: types.Message,  state: FSMContext):
    current_state = await state.get_state()
    if current_state != UserWriting.add_words:
        await state.set_state(UserWriting.add_words)
        await message.answer(f"Пишите мне слова, а я добавлю их в ваш личный словарь")
    else:
        await message.answer(f"Вы и так находитесь в режиме добавления слов в словарь")



@router.message(Command("print_dict"))
async def print_dict(message: types.Message):
    p_dictianory = "Ваш словарь:\n"
    user_words_ids = UserToWords.select(UserToWords.word_id).where(UserToWords.user_id == message.from_user.id)
    words = Word.select().where(Word.id.in_(user_words_ids)).order_by(Word.en_word)
    for word in words:
        word_cor_count = word.correct
        word_count = word.count
        if word_count != 0:
            p_dictianory += word.en_word + " - " + word.ru_word + " " + str(int((word_cor_count / word_count) * 100)) + "%" + "\n"
        else:
            p_dictianory += word.en_word + " - " + word.ru_word + "\n"
    await message.answer(p_dictianory)


@router.message(Command("delete"))
async def delete_words(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != UserWriting.delete_words:
        await state.set_state(UserWriting.delete_words)
        await message.answer(f"Ваш режим переключен на удаление\nПишите мне слова, а я удалю их из вашего словаря")
    else:
        await message.answer(f"Вы и так находитесь в режиме удаления слов из словаря")


@router.message(Command("choose_learn"))
async def choose_learn(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Обычный",
        callback_data="сложность_диктанта_обычный"), types.InlineKeyboardButton(
        text="Продвинутый",
        callback_data="сложность_диктанта_продвинутый")   
    )
    await message.answer("Выберите уровень сложности диктанта", reply_markup=builder.as_markup())



@router.message(Command("choose_language"))
async def choose_language(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Английский",
        callback_data="диктант_язык_английский"), types.InlineKeyboardButton(
        text="Русский",
        callback_data="диктант_язык_русский")   
    )
    data  = await state.get_data()
    current_language= data['language']
    await message.answer(f"Выберите язык диктанта\nСейчас выбран {current_language}", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("диктант_язык"))
async def send_random_value(call: types.CallbackQuery, state: FSMContext):
    callback_message = call.data.split("_")
    language_choice = callback_message[-1]
    await state.update_data(language=language_choice)
    await call.answer(f'Язык диктанта изменён на {language_choice}')


@router.message(Command("start_conversation_with_ai"))
async def learning(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != UserWriting.ai_conversation:
        await state.set_state(UserWriting.ai_conversation)
        await message.answer("Напишите мне что-то, я вам отвечу")
    else:
        await message.answer("Разговор уже начат")


@router.callback_query(F.data.startswith("сложность_диктанта_"))
async def send_random_value(call: types.CallbackQuery, state: FSMContext):
    callback_message = call.data.split("_")[-1]
    await state.update_data(dictation_difficulty=callback_message)
    await call.answer(f'Сложность изменена на {callback_message}')


@router.message(Command("start_learning"))
async def learning(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    user_in = message.from_user.id
    language = data['language']
    if current_state != UserWriting.learning:
        if language == "английский":
            word_ru_en = "en_word"
            src = "en"
            dest = "ru"
        elif language == "русский":
            word_ru_en = "ru_word"
            src = "ru"
            dest = "en"
        user_words_ids = UserToWords.select(UserToWords.word_id).where(UserToWords.user_id == user_in)
        user_words = [i.en_word for i in Word.select().where(Word.id.in_(user_words_ids))]
        if len(user_words) < 10:
            await message.answer("Добавьте еще слов в словарь, чтобы начать диктант(нужно минимум 10 слов)")
        else:
            difficulty = (await state.get_data())['dictation_difficulty']
            if difficulty == "обычный":
                await message.answer("Готовы к диктанту?")
                await learn_main(message, state, user_words_ids, dest, user_id=user_in, n_questions=5)
            else:
                await message.answer("Готовы к диктанту?")
                await learn_main(message, state, user_words_ids, dest, user_id=user_in, n_questions=10)
            await state.set_state(UserWriting.learning)
    else:
        await message.answer("Диктант уже идет")


@router.message(Command("stop"))
async def stop(message: types.Message, state: FSMContext):
    global words_c, correct, HELP_MESSAGE
    current_state = await state.get_state()
    if current_state == UserWriting.learning:
        words_c = 0
        correct = 0
        await message.answer(f"Диктант окончен")
    elif current_state == UserWriting.tranlator_mode:
        await message.answer(f"Вы вышли из режима перевода")
    elif current_state == UserWriting.add_words:
        await message.answer(f"Вы больше не добавляете слова в словарь")
    elif current_state == UserWriting.delete_words:
        await message.answer(f"Вы больше не удаляете слова из словаря")
    else:
        await message.answer(f"Вы находитесь в режиме по-умочанию\nВыберите один из режимов работы\n{HELP_MESSAGE}")
    await state.set_state(None)

@router.message(UserWriting.ai_conversation)
async def ai_conversation_handler(message: types.Message, state: FSMContext):
    try:
        respond = await gpt_request(message=message.text)
        await message.answer(respond)
    except Exception as e:
        logging.warning("Временный лимит для Yandex API ещё не истек")
        await message.answer("Слишком много запросов в последнее время")       

@router.message(UserWriting.add_words)
async def add_words_handler(message: types.Message, user_in, state: FSMContext):
    try:
        spell_check = True
        scr = langid.classify(message.text)[0]
        ans = None
        if scr != 'ru':
            if spell(message.text) == message.text:
                lang = "en"
                ans = await translate(message.text, target_language='ru')
            else:
                ans = f"Вы ошиблись в написании слова\nВозможно вы имели в виду: {spell(message.text)}"
                spell_check = False
        else:
            lang = "ru"
            if spell(message.text) == message.text:
                ans = await translate(message.text, target_language='en')
            else:
                ans = f"Вы ошиблись в написании слова\nВозможно вы имели в виду: {spell(message.text)}"
                spell_check = False
        user_words_ids = UserToWords.select(UserToWords.word_id).where(UserToWords.user_id == user_in)
        if not spell_check:
            return await message.answer(ans)
        if scr != 'ru':
            if Word.select().where((Word.id.in_(user_words_ids)) & (Word.en_word == message.text)).exists():
                await message.answer("Извините, в вашем словаре уже есть это слово!")
            else:
                word = Word.create(en_word=message.text, ru_word=ans)
                word.save() 
                connection = UserToWords.create(user_id=user_in, word_id=word)
                connection.save()
                await message.answer(f"Слово {message.text} было успешно добавлено в ваш словарь!")                
        else:
            if Word.select().where((Word.id.in_(user_words_ids)) & (Word.ru_word == message.text)).exists():
                await message.answer("Извините, в вашем словаре уже есть это слово!")
            else:
                word = Word.create(en_word=ans, ru_word=message.text)
                word.save()
                connection = UserToWords.create(user_id=user_in, word_id=word)
                connection.save()
                await message.answer(f"Слово {ans} было успешно добавлено в ваш словарь!")               
    except Exception as e:
        logging.error(e)
        logging.error("AIM token is likely expired")
        await message.answer("Что то пошло не так")


@router.message(UserWriting.tranlator_mode)
async def ai_conversation_handler(message: types.Message, user_in, state: FSMContext):
    try:
        scr = langid.classify(message.text)[0]
        if scr != 'rus':
            lang = "ru"
            if spell(message.text) == message.text:
                ans = await translate(message.text, target_language=lang)
            else:
                ans = f"Вы ошиблись в написании слова\nВозможно вы имели в виду: {spell(message.text)}"
        else:
            lang = "en"
            if spell(message.text) == message.text:
                ans = await translate(message.text, target_language=lang)
            else:
                ans = f"Вы ошиблись в написании слова\nВозможно вы имели в виду: {spell(message.text)}"
        user_in = message.from_user.id
        await message.answer(ans)
    except Exception as e:
        logging.error(e)
        logging.error("AIM token is likely expired")
        await message.answer("Что то пошло не так")


@router.message(UserWriting.delete_words)
async def delete_words_handler(message: types.Message, user_in, state: FSMContext):
    user_words_ids = UserToWords.select(UserToWords.word_id).where(UserToWords.user_id == user_in)
    try:
        scr = langid.classify(message.text)[0]
        if scr != "ru":
            word = Word.get_or_none((Word.id.in_(user_words_ids)) & (Word.en_word == message.text))
            if word:
                word.delete_instance(recursive=True)
                await message.answer(f"Слово {message.text} было удалено из вашего словаря")
            else:
                await message.answer(f"Похоже, что слова {message.text} нет в вашем словаре")
        else:
            word = Word.get_or_none((Word.id.in_(user_words_ids)) & (Word.ru_word == message.text))
            if word:
                word.delete_instance(recursive=True)
                await message.answer(f"Слово {message.text} было удалено из вашего словаря")
            else:
                await message.answer(f"Похоже, что слова {message.text} нет в вашем словаре")
    except Exception as e:
        logging.error(e)
        logging.error("AIM token is likely expired")
        await message.answer("Что то пошло не так, попробуйте еще раз")


@router.message(F.text)
async def message_work(message: types.Message):
    await message.answer(f"Выберите режим работы\n{HELP_MESSAGE}")
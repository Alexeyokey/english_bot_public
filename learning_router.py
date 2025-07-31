from aiogram import Router, F, types
import logging
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from api.tokens_api import API_TOKEN, YANDEX_FOLDER_ID
import langid
from random import choice, randint, choices
from autocorrect import Speller
from api.yandex_api import translate, gpt_request
from db.database import User, Word, UserToWords
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


router = Router()


lang = "en"
spell = Speller(lang=lang)
user_in = None

words_count = 0
correct = 0
test_word = ""


class UserAnswerLearning(CallbackData, prefix='learn'):
    action: str
    word: str
    dest: str
    test_word_dest: str
    n_questions: int


async def show_test_words(message: types.Message, state: FSMContext, user_words_ids, dest, test_word_dest, n_questions):
    user_words = [i.en_word for i in Word.select().where(Word.id.in_(user_words_ids))]
    words_for_test = choices(user_words, k=3)
    builder = InlineKeyboardBuilder()
    test_word = await translate(choice(words_for_test), target_language=test_word_dest)
    await state.update_data(test_word=test_word)
    for word in words_for_test:
        word_translation = await translate(word, dest)
        builder.add(types.InlineKeyboardButton(
            text=word_translation,
            callback_data=UserAnswerLearning(action='answer', word=word, dest=dest, test_word_dest=test_word_dest, n_questions=n_questions).pack()))

    await message.answer(str(test_word) + '\nПожалуйста, введите соотвутсвующее слово слову выше', reply_markup=builder.as_markup())


@router.callback_query(UserAnswerLearning.filter(F.action == "answer"))
async def get_user_answer(callback: types.CallbackQuery, state: FSMContext, callback_data: dict):
    global test_word
    state_data = await state.get_data()
    test_word = state_data['test_word']
    words_count = state_data['words_count']
    correct = state_data['correct']
    user_ans = callback_data.word
    message = callback.message
    n_questions = callback_data.n_questions
    test_word_dest = callback_data.test_word_dest
    test_word_en = await translate(test_word, 'en')
    user_words_ids = UserToWords.select(UserToWords.word_id).where(UserToWords.user_id == user_in)
    word = Word.get_or_none((Word.id.in_(user_words_ids)) & (Word.en_word == test_word_en))
    user_ans = await translate(user_ans, test_word_dest)
    words_count += 1
    await state.update_data(words_count=words_count)
    if word:
        word_correct, word_count = word.correct, word.count
        word_count += 1
        if user_ans == test_word:
            await message.answer("Верно!")
            correct += 1
            await state.update_data(correct=correct)
            word_correct += 1
        else:
            await message.answer("Неверно")
        qry = Word.update({Word.correct: word_correct, Word.count: word_count}).where((Word.id.in_(user_words_ids)) & (Word.en_word == test_word))
        qry.execute()
        if words_count >= n_questions:
            await message.answer(f"Диктант завершен\nВы правильно перевели {correct}/{n_questions} слов")
            await state.set_state(None)
        else:
            await show_test_words(message, state, user_words_ids, callback_data.dest, test_word_dest, n_questions)
        await callback.answer()
    else:
        callback.answer('Что-то пошло не так, мы не смогли найти выбранное вами слово в вашем')

async def learn_main(message: types.Message, state: FSMContext, user_words_ids, dest, user_id, n_questions=5):
    global user_in
    user_in = user_id
    if dest == 'ru':
        test_word_dest = 'en'
    else:
        test_word_dest = 'ru'
    await state.update_data(words_count=0)
    await state.update_data(correct=0)
    await show_test_words(message, state, user_words_ids, dest, test_word_dest, n_questions)

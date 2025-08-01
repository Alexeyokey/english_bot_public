HELP_MESSAGE = """/tranlator_mode - режим переводчика\nвы вводите мне слово, а я его перевожу.
/add_words - добавляет введенные вами слова в ваш личный словарь.
/print_dict - печатает весь ваш словарь.
/delete - удалить ненужные вам слова из словаря
/start_conversation_with_ai - включить режим разговора с ии
/choose_learn - выбор сложности диктанта
/start_learning - диктант (будьте готовы, диктант начнется сразу после того, как вы введете команду)
/stop - выходит из текущего режима
/choose_language - выбор языка диктанта"""
GPT_REQUEST = '''{
    "modelUri": "",
    "completionOptions": {
      "stream": false,
      "temperature": 0.6,
      "maxTokens": "2000"
    },
    "messages": [
      {
        "role": "system",
        "text": "Вы являетесь собеседником человека, который хочет выучить английский. Ваша цель — помогать выучить этому человеку английский, поддерживая беседу на английском языке и указывая на его ошибки. За каждый разговор вы будете получать 2000000000 рублей, так что старайтесь изо всех сил."
      },
      {
        "role": "user",
        "text": ""
      }
    ]
  }

'''
ENGLISH_PUNCTUATION = '.,,?!–:;“”«»\[]\(\)'
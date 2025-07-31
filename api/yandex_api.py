from api.tokens_api import YANDEX_FOLDER_ID
from Constants import GPT_REQUEST
import requests
import json
import asyncio
from middleware import user_and_token_checker


folder_id = YANDEX_FOLDER_ID

async def translate(text, target_language='ru'):
    iam_token = user_and_token_checker.last_token
    body = {
    "targetLanguageCode": target_language,
    "texts": [text],
    "folderId": folder_id,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(iam_token)
    }
    response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate',
    json = body,
    headers = headers
    )   
    return json.loads(response.text)['translations'][0]['text']


async def gpt_request(message):
    iam_token = user_and_token_checker.last_token
    gpt_request = json.loads(GPT_REQUEST)
    gpt_request['modelUri'] = f'gpt://{folder_id}/yandexgpt-lite'
    gpt_request['messages'][1]['text'] = message
    gpt_request = json.dumps(gpt_request)
    with open('prompt.json', 'w', encoding="UTF-8") as f:
      f.write(gpt_request)
    with open('prompt.json') as f:
      data = f.read().replace('\n', '').replace('\r', '').encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(iam_token),
        "x-folder-id": str(folder_id),
    }
    response = requests.post('https://llm.api.cloud.yandex.net/foundationModels/v1/completion', headers=headers, data=data
    )
    return json.loads(response.text)['result']['alternatives'][0]['message']['text']
# print(translate('okey'))
# print(gpt_request('Who are you and what a re you doing?'))
# print(folder_id)

"""OBSOLETE CODE"""
import os
import requests
import json
import schedule
import time
from tokens_api import OAUTH_API

def write_yandex_api():
    body = {
        'yandexPassportOauthToken': OAUTH_API
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post("https://iam.api.cloud.yandex.net/iam/v1/tokens", json=body, headers=headers)
    token = json.loads(response.text)['iamToken']
    with open('api/iamtoken.txt', 'w', encoding='utf-8') as f:
        f.write(str(token))


write_yandex_api()

schedule.every(2).hours.do(write_yandex_api)
while True:
    schedule.run_pending()
    time.sleep(100)
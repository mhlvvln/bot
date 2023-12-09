from dotenv import load_dotenv
import os
import requests
from json import loads

from database import get_config, create_session, set_config
from time import time

load_dotenv()

session = create_session()


def auth_token_request():
    """"
        Отправить запрос на получение токена
    """
    url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
    headers = {
        'Authorization': f'Bearer {os.getenv("auth_data")}',
        'RqUID': f'{os.getenv("client_server")}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    payload = {'scope': f'{os.getenv("scope")}'}
    response = requests.post(url, headers=headers, data=payload, verify=False)

    response = loads(response.text)
    print(response)
    set_config(session, normalize_unix(response['expires_at']), 1800, response['access_token'])
    return response


def normalize_unix(unix: int):
    """"
        нормлизовать пришедшее время от Сбера, сократить три последних символа
    """
    unix = str(unix)
    formatted_unix = unix[:-3]
    return int(formatted_unix)


def getToken():
    """"
        вернуть токен, если в базе он действующий
        обратиться к сберу, если в базе просрочился
    """
    config_element = get_config(session)
    print(f"{config_element=}")
    if config_element:
        if time() >= config_element.expires_at:
            auth = auth_token_request()
            return auth['access_token']
        else:
            return config_element.access_token
    else:
        return auth_token_request()['access_token']

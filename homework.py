import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import HTTPStatusNot200

ADDRESS = r'\main.log'

logging.basicConfig(
    level=logging.DEBUG,
    filename=os.path.expanduser('~') + ADDRESS,
    format='%(asctime)s, %(levelname)s, %(message)s'
)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_YANDEX')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщений в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Succesful send')
    except telegram.error.BadRequest:
        logging.error('Wrong chat id token')
    except Exception as error:
        logging.exception(f'Cant send due to {error}')


def get_api_answer(current_timestamp):
    """Делаем запрос и возвращаем ответ."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            status_code = response.status_code
            logging.error(f'Status code is not 200: {status_code}')
            raise HTTPStatusNot200
        else:
            return response.json()
    except Exception as error:
        logging.exception(f'Problem with ENDPOINT: {error}')
        raise


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        if type(response) is not dict:
            raise TypeError
        homework = response.get('homeworks')
        if type(homework) is not list:
            raise TypeError
        return homework
    except AttributeError:
        pass


def parse_status(homework):
    """Проверяет ответ API."""
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework:
        logging.error('Homework_name is not a homework key')
        raise KeyError

    homework_status = homework.get('status')
    if 'status' not in homework:
        logging.error('Status is not a homework key')
        raise KeyError

    if homework_status not in HOMEWORK_STATUSES.keys():
        logging.error(f'Status {homework_status} not in HOMEWORK_STATUSES')
        raise ValueError

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности токенов."""
    TOKENS_LIST = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    for var in TOKENS_LIST:
        if var is None:
            logging.critical(f'No token {var}')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        if bot.id:
            logging.info('Bot initialize succesful')
        else:
            logging.info('Bot doesnt initialize')
        current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Some problems: {error}'
            logging.exception(error)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

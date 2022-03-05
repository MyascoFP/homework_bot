from http import HTTPStatus
import requests
import time
import os
from dotenv import load_dotenv
import telegram
import logging


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
    filemode='w'
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
        pass
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

        else:
            return response.json()
    except Exception as error:
        logging.exception(f'Problem with ENDPOINT: {error}')
        raise


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        homework = response['homeworks']
        return homework
    except TypeError:
        logging.error('Problems with API')


def parse_status(homework):
    """Проверяет ответ API."""
    try:
        homework_name = homework[0].get('homework_name')
        homework_status = homework[0].get('status')

        verdict = HOMEWORK_STATUSES[homework_status]

        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except TypeError:
        logging.error('Problems with API')
    except IndexError:
        pass
    except KeyError:
        logging.error('Status not in HOMEWORK_STATUSES')


def check_tokens():
    """Проверка доступности токенов."""
    TOKENS_LIST = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    for var in TOKENS_LIST:
        if var is None:
            logging.critical(f'отсутствует токен {var}')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            message = parse_status(homeworks)
            send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(error)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

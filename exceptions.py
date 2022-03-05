import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s'
)

class HTTPStatusNot200:
    logging.error('Статус API не 200')
from json.decoder import JSONDecodeError
import os
import time
import requests
import logging
from requests.exceptions import RequestException
import telegram
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRACTICUM_HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

PRACTICUM_HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


def send_message(bot, message):
    """Отправка статуса."""
    logging.info(f'message send {message}')
    try:
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        logging.error(e, exc_inf=True)


def get_api_answer(url, current_timestamp):
    """Получение статуса."""
    headers = PRACTICUM_HEADERS
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(url, headers=headers, params=payload)
    except RequestException as e:
        logging.error(e, exc_inf=True)
    if homework_statuses.status_code != 200:
        raise Exception('invalid response')
    logging.info('server respond')
    try:
        return homework_statuses.json()
    except JSONDecodeError:
        return {}


def parse_status(homework):
    """Распознование статуса."""
    verdict = PRACTICUM_HOMEWORK_STATUSES[homework.get('status')]
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise Exception('No homework name')
    if verdict is None:
        raise Exception('No verdict')
    logging.info(f'got verdict {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


class EmptyResponse(Exception):
    pass


def check_response(response):
    """Проверка."""
    hws = response.get('homeworks')
    if not hws:
        raise EmptyResponse
    if hws[0].get('status') not in PRACTICUM_HOMEWORK_STATUSES:
        raise Exception('Статус неизвестен')
    return hws[0]


def main():
    """Главная."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            get_api_answer_result = get_api_answer(ENDPOINT, current_timestamp)
            check_response_result = check_response(get_api_answer_result)
            if check_response_result:
                parse_status_result = parse_status(check_response_result)
                send_message(bot, parse_status_result)
            time.sleep(RETRY_TIME)
        except EmptyResponse:
            pass
        except Exception as e:
            logging.error('Bot fall')
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID, text=f'Сбой в работе программы: {e}'
            )
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

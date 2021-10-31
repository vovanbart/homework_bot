import os
import time
import requests
import logging
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
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


def send_message(bot, message):
    logging.info(f'message send {message}')
    return bot.send_message(chat_id=CHAT_ID, text=message)


def get_api_answer(url, current_timestamp):
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    homework_statuses = requests.get(url, headers=headers, params=payload)
    if homework_statuses.status_code != 200:
        raise Exception("invalid response")
    logging.info('server respond')
    return homework_statuses.json()


def parse_status(homework):
    verdict = HOMEWORK_STATUSES[homework.get('status')]
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise Exception("No homework name")
    if verdict is None:
        raise Exception("No verdict")
    logging.info(f'got verdict {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    hws = response.get('homeworks')
    if hws is None:
        raise Exception("No homeworks")
    if (type(hws) != list) and (len(hws) == 0):
        raise Exception("Wrong type of homework")
    for hw in hws:
        status = hw.get('status')
        if status in HOMEWORK_STATUSES.keys():
            return hws
        else:
            raise Exception("no such status")
    return hws


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    url = ENDPOINT
    while True:
        try:
            get_api_answer_result = get_api_answer(url, current_timestamp)
            check_response_result = check_response(get_api_answer_result)
            if check_response_result:
                for homework in check_response_result:
                    parse_status_result = parse_status(homework)
                    send_message(bot, parse_status_result)
            time.sleep(RETRY_TIME)
        except Exception as error:
            logging.error('Bot fall')
            bot.send_message(
                chat_id=CHAT_ID, text=f'Сбой в работе программы: {error}'
            )
            time.sleep(RETRY_TIME)
            continue


if __name__ == '__main__':
    main()

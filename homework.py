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
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
current_timestamp = time.time()
PAYLOAD = {'from_date': current_timestamp}

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


def send_message(bot, message):
    """Отправка статуса."""
    logging.info(f'message send {message}')
    try:
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except requests.ConnectionError as e:
        logging.info(e) 


def get_api_answer(url): 
    """Получение статуса.""" 
    headers = HEADERS
    payload = PAYLOAD
    try:
        homework_statuses = requests.get(url, headers=headers, params=payload)
    except requests.ConnectionError as e:
        logging.info(e) 
    if homework_statuses.status_code != 200: 
        raise Exception('invalid response') 
    logging.info('server respond') 
    return homework_statuses.json() 


def parse_status(homework):
    """Распознование статуса."""
    verdict = HOMEWORK_STATUSES[homework.get('status')]
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise Exception('No homework name')
    if verdict is None:
        raise Exception('No verdict')
    logging.info(f'got verdict {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    """Проверка."""
    hws = response.get('homeworks')
    if hws is None:
        raise Exception('No homeworks')
    if type(hws) != list and len(hws) == 0:
        raise Exception('Wrong type of homework')
    for hw in hws:
        status = hw.get('status')
        if status in HOMEWORK_STATUSES:
            return hw
        else:
            raise Exception('no such status')
    return hws


def main():
    """Главная."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            get_api_answer_result = get_api_answer(ENDPOINT)
            check_response_result = check_response(get_api_answer_result)
            if check_response_result:
                for homework in check_response_result:
                    parse_status_result = parse_status(homework)
                    send_message(bot, parse_status_result)
            time.sleep(RETRY_TIME)
        except Exception as error:
            logging.error('Bot fall')
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID, text=f'Сбой в работе программы: {error}'
            )
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

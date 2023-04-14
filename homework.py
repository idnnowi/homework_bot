"""Бот для отправки изменения статуса проверки задания."""
import os
import requests
import logging
import time
import telegram

from dotenv import load_dotenv
from http import HTTPStatus
from exceptions import (
    HttpResponseError,
    RequestError,
    StatusIsNotOK,
    TokenCheckError,
)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('HW_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_TOKEN')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


TOKENS_NAMES = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')


def check_tokens():
    """Проверка токенов окружения."""
    for name in TOKENS_NAMES:
        if not globals()[name]:
            logging.critical('Токен не задан!')
            raise TokenCheckError('Токен не задан!', name)
    logging.debug('Токены заданы.')


def send_message(bot, message):
    """Отправка сообщениня в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообшение отправленно успешно.')
    except telegram.error.TelegramError as error:
        logging.exception(f'Не удалось отправить {message}')
        raise (
            HttpResponseError('Ошибка API Telegram Bot.', HTTPStatus.CONFLICT)
        ) from error


def get_api_answer(timestamp):
    """Запрос к API практикума."""
    try:
        homework = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
    except requests.RequestException:
        logging.exception('Ошибка ответа API.')
        raise RequestError('Ошибка ответа API.', HTTPStatus.CONFLICT)
    homework_json = homework.json()
    if homework.status_code != HTTPStatus.OK:
        if set(homework_json) == {'error', 'code'}:
            logging.exception('Ошибка со стороны API')
            raise StatusIsNotOK(
                'Ошибка со стороны API', homework_json.get('error')
            )
        logging.exception('Проблемы со стороны API.')
        raise HttpResponseError(
            'Проблемы со стороны API.', homework.status_code
        )
    logging.debug('Статус API code: 200.')
    return homework_json


def check_response(response: dict) -> list:
    """Проверка ответа API."""
    if not isinstance(response, dict):
        logging.exception('Ответ не является словарём.')
        raise TypeError('Ответ не является словарём.')

    if 'homeworks' not in response:
        logging.exception('Ответ API пустой!')
        raise KeyError('Ответ API пустой!')

    if not isinstance(response['homeworks'], list):
        logging.exception('Ответ не является списком.')
        raise TypeError('Ответ не является списком.')


def parse_status(homework):
    """Проверка изменения статуса проекта."""
    if 'homework_name' in homework:
        homework_name = homework.get('homework_name')
        status = homework.get('status')
        if status not in HOMEWORK_VERDICTS:
            logging.exception('Неизвестный статус.')
            raise KeyError('Неизвестный статус.')
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logging.exception('Отсутствует homework_name.')
    raise KeyError('Отсутствует homework_name.')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            request = get_api_answer(timestamp)
            check_response(request)
            timestamp = request['current_date']
            if request['homeworks']:
                message = parse_status(request.get('homeworks')[0])
                send_message(bot, message)
            else:
                logging.debug('Status has not changed')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        filemode='w',
        encoding='utf-8',
        format='%(asctime)s %(levelname)s %(message)s',
    )
    main()

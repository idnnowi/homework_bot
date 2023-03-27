"""Бот для отправки изменения статуса проверки задания."""
import os
import requests
import logging
import time
import telegram

from dotenv import load_dotenv
from http import HTTPStatus
from exceptions import HttpResponseError, RequestError, TokenIsNoneError

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    encoding='utf-8',
    format='%(asctime)s %(levelname)s %(message)s',
)

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


def check_tokens():
    """Проверка токенов окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if token is None:
            logging.critical('Токен %(token)s не задан!')
            raise TokenIsNoneError('Токен %(token)s не задан!')


def send_message(bot, message):
    """Отправка сообщениня в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообшение отправленно успешно.')
    except Exception as error:
        logging.error(f'Не удалось отправить {message}')
        raise (HttpResponseError('Ошибка API Telegram Bot.')) from error


def get_api_answer(timestamp):
    """Запрос к API практикума."""
    try:
        homework = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        if homework.status_code is HTTPStatus.OK:
            logging.debug('Статус API code: 200.')
            return homework.json()
        logging.error('Проблемы со стороны API.')
        raise HttpResponseError('Проблемы со стороны API.')
    except requests.RequestException:
        logging.error('Ошибка ответа API.')
        raise RequestError('Ошибка ответа API.')


def check_response(response: dict) -> list:
    """Проверка ответа API."""
    if not isinstance(response, dict):
        logging.error('Ответ не является словарём.')
        raise TypeError('Ответ не является словарём.')

    if 'homeworks' not in response:
        logging.error('Ответ API пустой!')
        raise KeyError('Ответ API пустой!')

    if not isinstance(response['homeworks'], list):
        logging.error('Ответ не является списком.')
        raise TypeError('Ответ не является списком.')
    return response.get('homeworks')[0]


def parse_status(homework):
    """Проверка изменения статуса проекта."""
    if 'homework_name' in homework:
        homework_name = homework.get('homework_name')
        status = homework.get('status')
        if status not in HOMEWORK_VERDICTS:
            logging.error('Неизвестный статус.')
            raise KeyError('Неизвестный статус.')
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logging.error('Отсутствует homework_name.')
    raise KeyError('Отсутствует homework_name.')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            request = get_api_answer(timestamp)
            homework = check_response(request)
            message = parse_status(homework)
            send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

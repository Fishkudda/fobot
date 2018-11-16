"""
Friends Only Server Bot.
Alpha 0.0.1
"""


from TelegramBot import TelegramBot
import os
import time
import telegram

SCREEN_NAME = str(os.environ.get('SCREEN_NAME'))


def set_init_screen_id():
    screen_id = ""
    os.system('screen -ls > /tmp/screenoutput')
    with open('/tmp/screenoutput', 'r') as file:
        result = file.readlines()

    if (result[0] == 'There is a screen on:\r\n') or (
            result[0] == 'There are screens on:\n') or (
            result[0] == 'There is a screen on:\n'):

        for index, line in enumerate(result):
            if SCREEN_NAME in line:
                split_res = result[index].split('.')[0]
                screen_id = split_res.strip('\t')

    return screen_id


def check_screen_id(old):
    os.system('screen -ls > /tmp/screenoutput')
    with open('/tmp/screenoutput', 'r') as file:
        result = file.readlines()

    screen_id = ""

    if (result[0] == 'There is a screen on:\r\n') or (
            result[0] == 'There are screens on:\n') or (
            result[0] == 'There is a screen on:\n'):

        for index, line in enumerate(result):
            if SCREEN_NAME in line:
                split_res = result[index].split('.')[0]
                screen_id = split_res.strip('\t')

    if screen_id == old:
        return True
    else:
        return False


token = str(os.environ.get('BOT_TOKEN'))
chat_id = os.environ.get('CHAT_ID')
SCREEN_NAME = os.environ.get('SCREEN_NAME')
screen_id_old = set_init_screen_id()

#bot = TelegramBot(token=token,chat_id=chat_id)
try:
    bot = TelegramBot(token=token,chat_id=chat_id)

except telegram.error.TimedOut:
    print('Telegram Timeout Error')

except telegram.error.RetryAfter:
    print('Telegram Retry Error')

except Exception:
    os.system('screen -X -S fobot kill')


while True:
    time.sleep(5)
    print('Server is running on: Screen ID: {}'.format(screen_id_old))
    if not check_screen_id(screen_id_old):
        os.system('screen -X -S fobot kill')


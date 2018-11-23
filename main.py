"""
Friends Only Server Bot.
Alpha 0.0.1
"""


from TelegramBot import TelegramBot
import os
import time as t
import sys
import telegram
import threading

SCREEN_NAME = str(os.environ.get('SCREEN_NAME'))
bot = None
DEBUG = True

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

try:
    bot = TelegramBot(token=token,chat_id=chat_id,debug=DEBUG)
except Exception as GeneralExeption:
    print(GeneralExeption)
    os.system('screen -X -S fobot kill')





def screen_daemon(inter):
        class Screen_Thread(threading.Thread):

            def __init__(self, interval):
                threading.Thread.__init__(self)
                self.interval = interval

            def run(self):
                while True:
                    try:
                        if not check_screen_id(screen_id_old):
                            os.system('screen -X -S fobot kill')
                        t.sleep(self.interval)
                    except Exception as ScreenCheckException:
                        if bot and DEBUG:
                            bot.dispatcher.bot.sendMessage(chat_id=chat_id,text=str(ScreenCheckException))
                        os.system('screen -X -S fobot kill')

        return Screen_Thread(inter).start()

screen_daemon(3)
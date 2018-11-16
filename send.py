from main import bot
import os
import sys

token = str(os.environ.get('BOT_TOKEN'))
chat_id = os.environ.get('CHAT_ID')

bot.dispatcher.bot.sendMessage(chat_id=chat_id,text=sys.argv[1])
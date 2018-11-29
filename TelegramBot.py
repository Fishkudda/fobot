from telegram.ext import Updater, Filters, MessageHandler, CommandHandler, CallbackQueryHandler
import os
from Server import Server
import telegram
import Database
import re
import math
import time
import requests
import io
import shutil

ADMINS = [651421362,742523989,85438832]
USERS = [651421362,742523989,85438832]

class TelegramBot:
    def __init__(self, token, chat_id,debug=False):
        self.token = token
        self.updater = Updater(
            token=token)
        self.updater.start_polling()
        self.dispatcher = self.updater.dispatcher
        self.id = self.updater.bot.id
        self.username = self.updater.bot.username
        self.token = token
        self.chat_id = chat_id
        self.admins = ADMINS
        self.users = USERS
        self.status = {}
        self.server = Server(telegram_bot=self)
        self.debug = debug
        self.menu_reg = ['Status',
                         'Maplist',
                         'Move',
                         'Ban',
                         'Kick',
                         'DB Size',
                         'Map Stats',
                         'Players']
        self.talk = False



        # Command Handler
        handle_player_move = CommandHandler('move',self.move_player)
        handle_server_status = CommandHandler('status',self.server_status)
        handle_help = CommandHandler('help',self.help)
        handle_server_down = CommandHandler('down',self.server_down)
        handle_server_up = CommandHandler('up',self.server_up)
        handle_server_restart = CommandHandler('restart',self.server_restart)
        handle_map_list = CommandHandler('maplist',self.map_list)
        handle_say = CommandHandler('say',self.just_say)
        handle_kick = CommandHandler('kick',self.kick_id)
        handle_sync = CommandHandler('ban',self.ban_player)
        handle_send_id = CommandHandler('get_id',self.get_id)
        handle_get_chat_id = CommandHandler('get_chat_id',self.get_chat_id)
        handle_get_full_log = CommandHandler('get_full_log',self.get_full_log)
        handle_db_size = CommandHandler('get_db_size',self.db_size)
        handle_get_maps_stats = CommandHandler('maplist_stats',self.map_stats)
        handle_get_all_players = CommandHandler('getPlayers',self.get_all_player)
        handle_bot = CommandHandler('bot',self.bot_menu)
        handle_set_vip = CommandHandler('set_vip',self.set_vip)
        handle_unset_vip = CommandHandler('unset_vip',self.unset_vip)
        handle_total_up = CommandHandler('total_up',self.total_up)
        handle_talk = CommandHandler('talk',self.toogle_talk)
        handle_introduce = CommandHandler('introduce',self.introduce_yourself)
        handle_cfg_loader = CommandHandler('load_cfg',self.cfg_loader)

        # Message Handler
        message_handler = MessageHandler(Filters.text, self.request_update)
        file_handler = MessageHandler(Filters.document,self.upload_file)

        self.dispatcher.add_handler(handle_send_id)
        self.dispatcher.add_handler(handle_get_chat_id)
        self.dispatcher.add_handler(message_handler)
        self.dispatcher.add_handler(handle_help)
        self.dispatcher.add_handler(handle_server_status)
        #self.dispatcher.add_handler(handle_server_down)
        #self.dispatcher.add_handler(handle_server_up)
        self.dispatcher.add_handler(handle_server_restart)
        self.dispatcher.add_handler(handle_kick)
        self.dispatcher.add_handler(handle_map_list)
        self.dispatcher.add_handler(handle_say)
        self.dispatcher.add_handler(handle_sync)
        if self.debug:
            self.dispatcher.bot.sendMessage(chat_id=self.chat_id, text="Fobot_restarted,DEBUG: {}".format(self.debug))
        self.dispatcher.add_handler(handle_player_move)
        self.dispatcher.add_handler(handle_db_size)
        self.dispatcher.add_handler(handle_get_maps_stats)
        self.dispatcher.add_handler(handle_get_all_players)
        self.dispatcher.add_handler(handle_bot)
        self.dispatcher.add_handler(handle_set_vip)
        self.dispatcher.add_handler(handle_unset_vip)
        self.dispatcher.add_handler(handle_total_up)
        self.dispatcher.add_handler(handle_talk)
        self.dispatcher.add_handler(handle_introduce)
        self.dispatcher.add_handler(handle_cfg_loader)
        self.dispatcher.add_handler(file_handler)


    def upload_file(self,bot,update):
        message_id = update._effective_message.message_id
        userid = update.message.from_user.id

        if userid not in self.admins:
            return False

        file_name = update.message.document.file_name
        file_type = update.message.document.mime_type
        file_id = update.message.document.file_id
        file_size = update.message.document.file_size

        get_file_path = "https://api.telegram.org/bot{}/getFile?file_id={}".format(self.token,file_id)

        result = requests.get(get_file_path)
        file_path = result.json()['result']['file_path']

        download_file = "https://api.telegram.org/file/bot{}/{}".format(self.token,file_path)

        download_file_result = requests.get(download_file, stream=True)

        file = io.BytesIO(download_file_result.content)

        if file_name.split('_')[0] != "fobot":
            return False

        if file_type == "text/x-csrc":
            path_to_save = "cfg_files/{}".format(file_name)
            with open(path_to_save,'wb') as f:
                f.write(file.read())
            msg = "{} uploaded".format(file_name)
            self.dispatcher.bot.sendMessage(chat_id=self.chat_id, text=msg)

            return msg



    def cfg_loader(self,bot,update):
        message_id = update._effective_message.message_id
        userid = update.message.from_user.id

        if userid not in self.admins:
            return False

        cfgs = FobotCfg.get_all_cfgs()
        custom_keyboard = []

        for key in cfgs:
            custom_keyboard.append([key])

        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                    selective=True,
                                                    one_time_keyboard=True)

        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        reply_to_message_id=message_id,
                                        text="Load Cfg")



    def introduce_yourself(self,bot,update):
        userid = update.message.from_user.id

        if userid not in self.admins:
            return False
        msg = [
            "Welcome to Friends Only Daddelstube",
            "Iam Fobot i serve the server community by tracking maps, handling server data and calculating the map pool",
            "Please help me and like maps with !like and dislike them with !dislike",
            "If you need support, please send a ticket example: !ticket [your problem]",
            ]

        for row in msg:
            self.server.just_say(row)
            time.sleep(3)


    def toogle_talk(self,bot,update):
        message_id = update._effective_message.message_id
        userid = update.message.from_user.id

        if (userid not in self.admins) and (userid not in self.admins):
            return False
        custom_keyboard = [['Activate'],['Deactivate']]

        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                    selective=True,
                                                    one_time_keyboard=True)
        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        text="Toogle Talk",
                                        reply_to_message_id=message_id)

    def total_up(self,bot,update):
        userid = update.message.from_user.id
        if userid not in self.admins:
            return False
        time_up = Database.get_total_minutes_up()
        self.dispatcher.bot.sendMessage(self.chat_id, "FOBOT TIME TRACKED FOR {} min".format(time_up))

    def set_vip(self,bot,update):
        message_id = update._effective_message.message_id
        if update.message.from_user.last_name:
            username = update.message.from_user.first_name + " " + update.message.from_user.last_name
        else:
            username = update.message.from_user.first_name
        userid = update.message.from_user.id
        if userid not in self.admins:
            return False
        custom_keyboard = []

        for player in self.server.get_players():
            custom_keyboard.append([player.name])
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                    selective=True,
                                                    one_time_keyboard=True)

        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        reply_to_message_id=message_id,
                                        text="Set Vip".format(username))

    def unset_vip(self,bot,update):
        message_id = update._effective_message.message_id
        if update.message.from_user.last_name:
            username = update.message.from_user.first_name + " " + update.message.from_user.last_name
        else:
            username = update.message.from_user.first_name
        userid = update.message.from_user.id
        if userid not in self.admins:
            return False
        custom_keyboard = []

        for player in self.server.get_players():
            custom_keyboard.append([player.name])
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                    selective=True,
                                                    one_time_keyboard=True)
        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        reply_to_message_id=message_id,
                                        text="Unset Vip".format(username))

    def help(self,bot,update):
        help_ms = """
Welcome i'am the Friend's Only Bot\n/s
I manage {}
\n
Please use me responsible\n
/bot - Bot Menu
/status - see server status\n
/maplist - change/see maps\n
/move - move player(hermy) to spectators\n
/kick - kick a player\n
/ban - ban a player\n  
/get_chat_id - get the chat id\n
/get_id - get your id\n   
/set_vip - set player vip\n
/unset_vip - unset vip\n
/total_up - time total tracked\n

""".format(os.environ.get('SERVER_NAME'))
        self.dispatcher.bot.sendMessage(self.chat_id, text=help_ms)

    def get_all_player(self,bot,update):
        userid = update.message.from_user.id

        if userid not in self.admins:
            return False

        players = Database.get_all_player()
        players = sorted(players, key=lambda time: Database.get_minutes_played(time),reverse=True)

        msg = ""

        for player in players:
            if re.match(r'^STEAM_',player.steam_id):
                try:
                    minutes_played = Database.get_minutes_played(player.id)
                except Exception as db_Exception:
                    minutes_played = "Cant get Time for Player"
                    print(db_Exception)
                msg = msg + player.name + '\n' + player.steam_id + '\nTime:{}min\n'.format(str(round(minutes_played)))+'Share: {}%\n'.format(round(Database.time_weight_player(player.id)))+'\n'

        partial = math.ceil(len(msg)/2000)

        part_msg = []

        if partial > 1:
            chunked = [players[i::partial]for i in range(partial)]

            for player_list in chunked:
                chunked_msg = ""
                for player in player_list:
                    if re.match(r'^STEAM_', player.steam_id):
                        minutes_played = Database.get_minutes_played(player.id)
                        print(minutes_played)
                        chunked_msg = chunked_msg + player.name + '\n' + player.steam_id +' Time:{}min'.format(str(round(minutes_played)))+ '\n'
                part_msg.append(chunked_msg)

        else:
            part_msg.append(msg)


        for msg_e in part_msg:
            self.dispatcher.bot.sendMessage(chat_id=self.chat_id, text=msg_e)
            time.sleep(3)

    def bot_menu(self,bot,update):
        message_id = update._effective_message.message_id
        userid = update.message.from_user.id

        if (userid not in self.admins) and (userid not in self.admins):
            return False
        custom_keyboard = []

        for entry in self.menu_reg:
            custom_keyboard.append([entry])
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                    selective=True,
                                                    one_time_keyboard=True)
        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        text="Menu",
                                        reply_to_message_id=message_id)

    def get_full_log(self):
        pass

    def map_stats(self,bot,update):
        userid = update.message.from_user.id

        if (userid not in self.admins) and (userid not in self.admins):
            return False

        maps = Database.get_maps_by_played()
        msg = "---Map List----\n"

        all_times = sum([the_map.played for the_map in maps])
        if all_times == 0:
            all_times = 1

        for the_map in maps:

            status_voted = Database.get_likes_dislikes(the_map)

            msg = msg + the_map.name+' share: '+str(round(the_map.played/all_times*100)) +'%\n'+'Liked:{}\nDisliked:{}\n'.format(status_voted[0],status_voted[1])

        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,text=msg)


    def db_size(self,bot,update):
        userid = update.message.from_user.id

        if userid not in self.admins:
            return False
        size = os.path.getsize('server.db')
        if size > 0:
            size = size / 1000000
        msg = "Size: {}MB".format(size)
        self.dispatcher.bot.sendMessage(self.chat_id,msg)

    def get_id(self,bot,update):
        self.dispatcher.bot.sendMessage(self.chat_id, text=update.message.from_user.id)

    def get_chat_id(self,bot,update):
        self.dispatcher.bot.sendMessage(chat_id=update.message.chat.id, text=update.message.chat.id)

    def request_update(self, bot, update):
        print(update)
        userid = update.message.from_user.id

        if (userid not in self.admins) and (userid not in self.admins):
            return False
        usecase = ""
        bot = update._effective_message.reply_to_message.from_user.is_bot

        if bot:
            usecase = update._effective_message.reply_to_message.text


        if usecase == "Change Map":
            self.server.change_level(update.message.text)
        if usecase == "Kick Player":
            for player in self.server.get_players():
                if player.name == update.message.text:
                    player.kick_player()
        if usecase == "BAN Player":
            for player in self.server.get_players():
                if player.name == update.message.text:
                    player.ban_player()
        if usecase == "Move Player":
            for player in self.server.get_players():
                if player.name == update.message.text:
                    player.to_spectators()
        if usecase == "Menu":
            if update.message.text == "Status":
                self.server_status(bot=bot,update=update)
            if update.message.text == "Maplist":
                self.map_list(bot=bot,update=update)
            if update.message.text == "Move":
                self.move_player(bot=bot,update=update)
            if update.message.text == "Kick":
                self.kick_id(bot=bot,update=update)
            if update.message.text == "DB Size":
                self.db_size(bot=bot,update=update)
            if update.message.text == "Ban":
                self.ban_player(bot=bot,update=update)
            if update.message.text == 'Map Stats':
                self.map_stats(bot=bot,update=update)
            if update.message.text == "Players":
                self.get_all_player(bot=bot, update=update)

        if usecase == "Load Cfg":
            result = self.server.load_cfg(FobotCfg.get_all_cfgs()[update.message.text])
            self.dispatcher.bot.sendMessage(self.chat_id,result)

        if usecase == 'Set Vip':
            res = Database.set_vip(update.message.text)
            print(res.vip)

        if usecase == 'Unset Vip':
            res = Database.unset_vip(update.message.text)
            print(res.vip)

        if usecase == 'Toogle Talk':
            if update.message.text == 'Activate':
                self.talk = True
            elif update.message.text == 'Deactivate':
                self.talk = False

    def just_say(self,bot,update):
        userid = update.message.from_user.id

        if userid not in self.admins:
            return False
        self.server.just_say(" ".join(update.message.text.split(' ')[1:]))

    def move_player(self,bot,update):
        message_id = update._effective_message.message_id
        userid = update.message.from_user.id
        if update.message.from_user.last_name:
            username = update.message.from_user.first_name + " " + update.message.from_user.last_name
        else:
            username = update.message.from_user.first_name

        if (userid not in self.admins) and (userid not in self.admins):
            return False
        custom_keyboard = []

        for player in self.server.get_players():
            custom_keyboard.append([player.name])
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                    selective=True,
                                                    one_time_keyboard=True)
        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        reply_to_message_id=message_id,
                                        text="Move Player")

    def kick_id(self,bot,update):
        message_id = update._effective_message.message_id
        userid = update.message.from_user.id
        if update.message.from_user.last_name:
            username = update.message.from_user.first_name + " " + update.message.from_user.last_name
        else:
            username = update.message.from_user.first_name

        if (userid not in self.admins) and (userid not in self.admins):
            return False
        custom_keyboard = []

        for player in self.server.get_players():
            custom_keyboard.append([player.name])
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,selective=True,one_time_keyboard=True)
        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        reply_to_message_id= message_id,
                                        text="Kick Player")

    def ban_player(self,bot,update):
        message_id = update._effective_message.message_id
        if update.message.from_user.last_name:
            username = update.message.from_user.first_name + " " + update.message.from_user.last_name
        else:
            username = update.message.from_user.first_name
        userid = update.message.from_user.id
        if userid not in self.admins:
            return False
        custom_keyboard = []

        for player in self.server.get_players():
            custom_keyboard.append([player.name])
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,selective=True,one_time_keyboard=True)
        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        reply_to_message_id=message_id,
                                        text="BAN Player".format(username))


    def sync_status(self,bot,update):
        pass

    def server_status(self,bot,update):
        msg = "-----Server Status-----\n"
        msg = msg + "map: {}\n".format(self.server.current_map)
        msg = msg + "players {}\n".format(self.server.get_number_of_players())
        msg = msg + "bots:{}\n".format(self.server.get_number_of_bots())
        msg = msg + '\n'
        for player in self.server.get_players():
            msg = msg + "{}\n".format(player.name)
        self.dispatcher.bot.sendMessage(chat_id=self.chat_id, text=msg)

    def map_list(self,bot,update):
        message_id = update._effective_message.message_id
        userid = update.message.from_user.id

        if (userid not in self.admins) and (userid not in self.admins):
            return False

        custom_keyboard = []

        for map_name in self.server.get_map_list():
            custom_keyboard.append([map_name])
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,selective=True,one_time_keyboard=True)
        self.dispatcher.bot.sendMessage(chat_id=self.chat_id,
                                        reply_markup=reply_markup,
                                        text="Change Map",
                                        reply_to_message_id=message_id)


    def server_restart(self,bot,update):
        pass

    def server_down(self,bot,update):
        pass


    def server_up(self,bot,update):
        pass

    def system_status(self,bot,update):
        pass


class FobotCfg:
    def __init__(self, path,name):
        self.path = path
        self.name = name
        self.description = self.get_description()

    def __repr__(self):
        return "Name:{} Description:{} Path{}".format(self.name,
                                                          self.description,
                                                          self.path)

    def get_description(self):
        try:
            text = ""
            with open(self.path) as file:
                cfg = file.readline()

            if len(cfg) < 2:
                return text

            if re.match(r'^//', cfg[0]):
                text = text + cfg[0][1:]
            if re.match(r'^//', cfg[1]):
                text = text +'\n'+ cfg[0][1:]
            return text
        except Exception as fail_to_get:
            print(fail_to_get)
            return ""

    @staticmethod
    def get_all_cfgs():
        current_directory = os.getcwd()
        walk_path = "{}/cfg_files/.".format(current_directory)
        cfgs = {}
        for root, dirs, files in os.walk(walk_path):
            for file in files:
                file_path = "{}/cfg_files/{}".format(current_directory,file)
                cfgs[file] = FobotCfg(path=file_path, name=file)
        return cfgs






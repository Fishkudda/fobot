import os
import re
import threading
import datetime
import time as t
import Database

PATH_TO_SERVER = str(os.environ.get('PATH_TO_SERVER'))
SERVER_NAME = str(os.environ.get('SERVER_NAME'))
SCREEN_NAME = str(os.environ.get('SCREEN_NAME'))


class Server:
    def __init__(self,telegram_bot):
        self.update_counter = 0
        self.screen_id = ""
        self.ip = ""
        self.name = ""
        self.options = ""
        self.current_map = ""
        self.players = []
        self.map_list = []
        self.cap_time = None
        self.telegram_bot = telegram_bot

        walk_dir = os.walk(PATH_TO_SERVER + "/csgo/maps")
        for x, y, z in walk_dir:
            for map in z:
                if map.split('.')[-1] == 'bsp':
                    map_name = map.split('.')[0]
                    self.map_list.append(map_name)

        Database.database_create_maps(self.map_list)

        # Update Once by Init

        self.update()

        # Set Timer to Update
        self.update_daemon = self.update_daemon(20)
        self.user_input_daemon = self.user_input_daemon(5)

    def __repr__(self):
        return "Server:{} on {} map: {} player: {} bots: {}".format(self.name,
                                                                    self.ip,
                                                                    self.current_map,
                                                                    self.get_number_of_players(),
                                                                    self.get_number_of_bots())

    def load_cfg(self, cfg):
        move_cfg = "cp {}  {}/csgo/cfg/{}".format(cfg.path, PATH_TO_SERVER,
                                                  cfg.name)
        res = os.system(move_cfg)
        if res != 0:
            return "Error cant move file from {} to {}".format_map(cfg.path, PATH_TO_SERVER)

        exec_cfg = "screen -S {} -X stuff 'exec {}\r'".format(self.screen_id,
                                                              cfg.name)
        res_exec = os.system(exec_cfg)

        if res_exec == 0:
            return "Executes {} Cfg".format(cfg.name)
        else:
            return "Error cant exec {}".format(cfg.name)



    def change_level(self, name_id):
        sys_var = "screen -S {} -X stuff 'changelevel {}\r'".format(
            self.screen_id,
            name_id)
        os.system(sys_var)

    def add_player(self, player):
        self.players.append(player)

    def just_say(self,message):
        sys_var = "screen -S {} -X stuff 'say {}\r'".format(
            self.screen_id,message)
        os.system(sys_var)


    def get_number_of_players(self):
        return len(
            [player for player in self.get_players() if not player.is_bot])

    def get_number_of_bots(self):
        return len([player for player in self.get_players() if player.is_bot])

    def get_players(self):
        return self.players

    def set_current_map(self, current_map):
        self.current_map = current_map

    def get_current_map(self):
        return self.current_map

    def get_map_list(self):
        return self.map_list

    def update_daemon(self, interval):

        class Update_Thread(threading.Thread):

            def __init__(self, interval, mother_class):
                threading.Thread.__init__(self)
                self.interval = interval
                self.mother_class = mother_class

            def run(self):
                while True:
                    try:
                        self.mother_class.update()
                        t.sleep(self.interval)
                    except Exception as Exception_update:
                        print(Exception_update)

        return Update_Thread(interval, self).start()

    def user_input_daemon(self,interval):
        class UserInputThread(threading.Thread):

            def __init__(self, interval, mother_class):
                threading.Thread.__init__(self)
                self.interval = interval
                self.mother_class = mother_class

            def run(self):
                while True:
                    try:
                        self.mother_class.user_input_update()
                        #t.sleep(self.interval)
                    except Exception as Exception_user_input:
                        print(Exception_user_input)

        return UserInputThread(interval, self).start()


    def user_input_update(self):
        os.system('screen -ls > /tmp/screenoutput')
        with open('/tmp/screenoutput', 'r') as file:
            result = file.readlines()

        self.screen_id = ""

        if (result[0] == 'There is a screen on:\r\n') or (
                result[0] == 'There are screens on:\n') or (
                result[0] == 'There is a screen on:\n'):

            for index, line in enumerate(result):
                if SCREEN_NAME in line:
                    split_res = result[index].split('.')[0]
                    screen_id = split_res.strip('\t')
                    self.screen_id = screen_id

        if self.screen_id == "":
            return False

        cap_time = "echo "+str(datetime.datetime.utcnow())+'\n'
        sys_var = "screen -S {} -X stuff '{}\r'".format(screen_id, cap_time)
        if not self.cap_time:
            self.cap_time = cap_time


        os.system(sys_var)
        path_to_screenlog = PATH_TO_SERVER + "/screenlog.0"

        output = []
        ret_counter = 4

        while (self.cap_time not in output) and (cap_time not in output) and (ret_counter >= 0):
            try:
                t.sleep(7)
                ret_counter = ret_counter - 1
                with open(path_to_screenlog, 'r') as file:
                    output = file.readlines()
            except Exception as Exception_get_log:
                print(Exception_get_log)
                ret_counter = ret_counter - 1

        if (self.cap_time not in output) or (cap_time not in output):
            return False

        output.reverse()
        end_index = None
        start_index = None
        data_input = None

        for index,line in enumerate(output):
            if line == self.cap_time:
                end_index = index
            elif line == cap_time:
                start_index = index

            if end_index and start_index:
                break

        if end_index and start_index:
            data_input = output[start_index:end_index]

        if not data_input:
            return False

        self.cap_time = cap_time

        player_list = Database.get_all_player()

        player_dic = {player.name: player for player in player_list}
        try:
            player_names = [re.escape(player.name+':') for player in player_list]
            j_names = r'|'.join(player_names)
        except Exception as Exception_create_regex:
            print("Fail creating regex")
            print(Exception_create_regex)
            return False

        msg = ""
        data_input.reverse()

        for line in data_input:

            if re.search(j_names, line) or re.match(r'Console:', line):
                msg = msg + "{}\n".format(line)
                if line.split(':')[-1].strip() == '!like':
                    name = line.split(':')[0].strip()
                    if '*DEAD*' in name:
                        name = "".join(name.split('*')[3:]).strip()
                    voted_msg = Database.create_votes(name, self.current_map, True)
                    self.just_say(voted_msg)
                if line.split(':')[-1].strip() == '!dislike':
                    name = line.split(':')[0].strip()
                    if '*DEAD*' in name:
                        name = "".join(name.split('*')[3:]).strip()
                    voted_msg = Database.create_votes(name,self.current_map, False)
                    self.just_say(voted_msg)

                index = 0
                name = line.split(':')[index].strip()

                if '*DEAD*' in name:
                    index = 3
                    name = "".join(name.split('*')[index:]).strip()
                print(name)

                if (name in player_dic.keys()) or (name == "Console"):
                    first_w = line.split(':')[index+1].split(' ')[1]
                    if '!ticket' == first_w:
                        self.telegram_bot.dispatcher.bot.sendMessage(
                            self.telegram_bot.chat_id, text="{} TICKET  FROM: {}\nTEXT: {}".format(datetime.datetime.utcnow().strftime('%c'),name,line))
                        self.just_say("Your Ticket {} was send.".format(name))

        if msg != "" and self.telegram_bot.talk:
            self.telegram_bot.dispatcher.bot.sendMessage(self.telegram_bot.chat_id, text=msg)

    def update(self):
        os.system('screen -ls > /tmp/screenoutput')
        with open('/tmp/screenoutput', 'r') as file:
            result = file.readlines()

        self.screen_id = ""

        if (result[0] == 'There is a screen on:\r\n') or (
                result[0] == 'There are screens on:\n') or (
                result[0] == 'There is a screen on:\n'):

            for index, line in enumerate(result):
                if SCREEN_NAME in line:
                    split_res = result[index].split('.')[0]
                    screen_id = split_res.strip('\t')
                    self.screen_id = screen_id

        if self.screen_id == "":
            return False

        sys_var = "screen -S {} -X stuff 'status\r'".format(screen_id)

        os.system(sys_var)
        t.sleep(10)
        path_to_screenlog = PATH_TO_SERVER + "/screenlog.0"

        with open(path_to_screenlog, 'r') as file:
            output = file.readlines()
        output.reverse()

        i = 0
        i_end = 0

        if '#end\n' in output:
            for index, line in enumerate(output):
                if line == "#end\n":
                    i = index
                if 'hostname:' in line:
                    i_end = index
                    break

        info_range = range(i, i_end)

        info_list = []
        for i in info_range:
            info_list.append(output[i])

        info_list.reverse()
        ip = ""
        name = SERVER_NAME

        for i, text in enumerate(info_list):
            s_text = text.split(' ')

            if 'map' == s_text[0]:
                current_map = s_text[-1].rstrip()

            if 'udp/ip' == s_text[0]:
                for tab in s_text:
                    if re.match(
                            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b:\d{5}',
                            tab):
                        ip = tab

        self.ip = ip
        self.name = name
        self.current_map = current_map

        try:
            status_db = Database.create_server_status_ticker(self)
        except Exception as Database_Exception:
            print(Database_Exception)
            print("Database Error cant save server_status")

        self.players = []

        for i, text in enumerate(info_list):
            s_text = text.split(' ')

            id = s_text[0].strip('#')
            id_f = 0

            if id == "":
                id_f = 1
                id = s_text[1]



            if 'BOT' in s_text:
                try:
                    name_start = 0
                    name_end = 0
                    for index, char in enumerate(s_text):
                        if ('"' in char) and (name_start == 0):
                            name_start = index
                        if 'BOT' == char:
                            name_end = index
                    name = " ".join(s_text[name_start:name_end]).strip('"')
                except:
                    name = 'UNKNOWN_PLAYER_BOT'

                is_bot = True
                player = Player(id=id, name=name, is_bot=is_bot,
                                server=self)

                steam_id = "NO_STEAM_ID_FOR_BOT_{}".format(name)

                Database.create_player_status(datetime.datetime.utcnow(),name,steam_id)

                self.add_player(player)
            elif re.match(r"^#[0-9]", s_text[0]):
                i = 0
                id = s_text[1].strip('#')
                try:
                    name = s_text[3]
                    while name[-1] != '"':
                        name = name + s_text[3 + i]
                        i = i + 1
                except:
                    name = 'UNKNOWN_PLAYER'

                steam_id = "NO_ID_{}".format(name)

                is_bot = False
                for tab in s_text:
                    if 'BOT' in tab:
                        is_bot = True
                    if re.match(r'^STEAM_',tab):
                        steam_id = tab


                player = Player(id=id, name=name, is_bot=is_bot,
                                server=self, steam_id=steam_id,
                                ip=s_text[-1])
                self.add_player(player)

                Database.create_player_status(datetime.datetime.utcnow(), name,
                                              steam_id)

            elif (s_text[0] == '#' and re.match(r'^[0-9]',s_text[2])):
                i = 0
                id = s_text[1].strip('#')
                try:
                    name = s_text[3]
                    while name[-1] != '"':
                        name = name + s_text[3 + i]
                        i = i + 1
                except:
                    name = 'UNKNOWN_PLAYER'
                steam_id = "NO_ID_{}".format(name)
                is_bot = False
                for tab in s_text:
                    if 'BOT' in tab:
                        is_bot = True
                    if re.match(r'^STEAM_',tab):
                        steam_id = tab

                name = name.strip('"')

                player = Player(id=id, name=name, is_bot=is_bot,
                                server=self, steam_id=steam_id,
                                ip=s_text[-1])

                Database.create_player_status(datetime.datetime.utcnow(), name,
                                              steam_id)

                self.add_player(player)



        print(str(self) + " " + datetime.datetime.utcnow().strftime(
            '%c') + " UPDATE DONE")

        self.update_counter = self.update_counter + 1
        #Database.calculate_next_map_pool()

        return self


class Player:
    def __init__(self, id, is_bot, name, server, steam_id=None, ip=None):
        self.id = id
        self.is_bot = is_bot
        self.name = name
        self.ip = ip
        self.server = server
        self.steam_id = steam_id

    def __repr__(self):
        return "Player: ID {} {}\n".format(self.id, self.name)

    def kick_player(self):
        screen_id = self.server.screen_id
        sys_var = "screen -S {} -X stuff 'kickid {}\r'".format(screen_id,
                                                               self.id)
        os.system(sys_var)
        return self

    def to_spectators(self):
        screen_id = self.server.screen_id
        sys_var = "screen -S {} -X stuff 'sm_spec #{}\r'".format(screen_id,
                                                                 self.id)
        os.system(sys_var)
        return self

    def ban_player(self):
        screen_id = self.server.screen_id
        sys_var = "screen -S {} -X stuff 'banid {}\r'".format(screen_id,
                                                               self.id)
        os.system(sys_var)
        return self


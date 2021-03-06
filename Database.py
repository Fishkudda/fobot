from pony.orm import *
from datetime import datetime,timedelta
import re
from collections import OrderedDict

db = Database()


class Maps(db.Entity):
    id = PrimaryKey(int, auto=True)
    first_played = Required(datetime)
    last_played = Required(datetime)
    name = Required(str,unique=True)
    mode_type = Required(str)
    played = Required(int, sql_default=True, default=0)
    status = Set('ServerStatus')
    votes = Set('Votes')
    down_votes = Set('DownVotes')
    value = Required(int, sql_default=True, default=1000)


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    first_saw = Required(datetime)
    steam_id = Required(str,unique=True)
    name = Required(str)
    voted_up = Set('Votes')
    down_voted = Set('DownVotes')
    player_status = Set('PlayerStatus')
    multi = Required(int, sql_default=True, default=1)
    vip = Required(bool, sql_default=True, default=False)


class PlayerStatus(db.Entity):
    id = PrimaryKey(int, auto=True)
    time = Required(datetime,sql_default=True,default=datetime.utcnow())
    player = Required('Player')


class Votes(db.Entity):
    id = PrimaryKey(int, auto=True)
    voted = Required('Maps')
    player = Required('Player')


class DownVotes(db.Entity):
    id = PrimaryKey(int,auto=True)
    voted = Required('Maps')
    player = Required('Player')


class ServerStatus(db.Entity):
    id = PrimaryKey(int, auto=True)
    date = Required(datetime)
    bots = Required(int)
    human = Required(int)
    current_map = Required('Maps')


db.bind(provider="sqlite", filename='server.db', create_db=True)
db.generate_mapping(create_tables=True)
set_sql_debug(False)

@db_session
def get_likes_dislikes(the_map):
    down_voted = len(select(map_v for map_v in DownVotes if map_v.voted == the_map))
    up_voted = len(select(map_v for map_v in Votes if map_v.voted == the_map))
    return (up_voted, down_voted)


@db_session
def create_votes(name,map,choice):
    if name == "Console":
        if not Player.exists(name=name):
            player = add_player(datetime.utcnow(),name,steam_id='STEAM_TEST_CONSOLE')
        else:
            player = Player.get(name=name)
    else:
        player = Player.get(name=name)
    map_voted = Maps.get(name=map)

    if choice:
        if DownVotes.exists(player=player, voted = map_voted):
            ex_vote = DownVotes.get(player=player, voted=map_voted)
            ex_vote.delete()
        if Votes.exists(player=player, voted=map_voted):
            ex_vote = Votes.get(player=player, voted=map_voted)
            ex_vote.delete()
            return "Player {} does not like to play {} anymore".format(player.name,map_voted.name)
        Votes(voted=map_voted, player=player)
        return "Player {} likes to play {}".format(player.name,map_voted.name)
    else:
        if Votes.exists(player=player,voted=map_voted):
            ex_vote = Votes.get(player=player,voted=map_voted)
            ex_vote.delete()
        if DownVotes.exists(player=player, voted=map_voted):
            ex_vote = DownVotes.get(player=player,voted=map_voted)
            ex_vote.delete()
            return "Player {} does not dislike to play {} anymore".format(player.name,map_voted.name)
        DownVotes(voted=map_voted, player=player)
        return "Player {} dislikes to play {}".format(player.name,map_voted.name)


@db_session
def set_vip(player):
    if type(player) == str:
        if re.match(r'^STEAM_',player):
            player_steam_id = player
            p = Player.get(steam_id= player_steam_id)
            p.vip = True
            return p
        else:
            player_name = player
            p = Player.get(name=player_name)
            p.vip = True
            return p

    elif type(player) == int:
        player_id = player
        p = Player.get(id=player_id)
        p.vip = True
        return p

    elif type(player) == Player:
        player_db = player
        player_db.vip = True
        return player_db


@db_session
def unset_vip(player):
    if type(player) == str:
        if re.match(r'^STEAM_', player):
            player_steam_id = player
            p = Player.get(steam_id=player_steam_id)
            p.vip = False
            return p
        else:
            player_name = player

            p = Player.get(name=player_name)
            p.vip = False
            return p

    elif type(player) == int:
        player_id = player
        p = Player.get(id=player_id)
        p.vip = False
        return p

    elif type(player) == Player:
        player_db = player
        player_db.vip = False
        return player_db


@db_session
def get_total_minutes_up():
    res = select(status for status in ServerStatus)
    return (len(res)*30)/60


@db_session
def get_minutes_players():
    all_player = select(player for player in Player if player.steam_id[0] != 'N')
    return sum([get_minutes_played(player)for player in all_player])

@db_session
def calculate_next_map_pool(list_of_players):
    list_of_players = [Player.get(steam_id=player.steam_id) for player in list_of_players if not player.is_bot]
    all_maps = get_maps_by_played()
    all_times_played = sum([map_v.played for map_v in all_maps])
    if all_times_played == 0:
        return [Maps.get(name='de_dust2'),Maps.get(name='cs_office')]

    maps_value_list =[]
    for map_v in all_maps:
        map_value = 0
        list_of_players = sorted(list_of_players,key=lambda time: get_minutes_played(time),reverse=True)

        for index,player in enumerate(list_of_players):
            res = map_v.value
            vip = player.vip
            player_liked_map = Votes.exists(player=player, voted=map_v)
            player_disliked_map = DownVotes.exists(player=player, voted=map_v)

            if player_liked_map:
                if vip:
                    res = res*1.3
                else:
                    res = res*1.2

            if player_disliked_map:
                if vip:
                    res = res*0.7
                else:
                    res = res*0.8

            if index in [0,1,2,3]:
                res = res * 1.2
            elif index in [4 , 5, 6, 7]:
                res = res * 1
            elif index in [8,9,10,11]:
                res = res * 0.9
            elif index in [12,13,14,15,16]:
                res = res*0.8
            else:
                res = res*0.7

            map_value = map_value + res

        maps_value_list.append((map_value,map_v))

    def take_value(entry):
        return entry[1]

    sorted_by_value = sorted(maps_value_list, key=take_value, reverse=True)
    print(sorted_by_value)
    result_list= []
    for i in range(3):
        result_list.append(sorted_by_value[i][0])
    print(result_list)
    return result_list



@db_session
def time_weight_player(player):

    all_player_time = get_minutes_players()

    if all_player_time == 0:
        return 0

    if type(player) == str:
        if re.match(r'^STEAM_', player):
            p = Player.get(steam_id=player)
            p_t = get_minutes_played(p)

            return (p_t/all_player_time)*100
        else:
            p = Player.get(name=player)
            p_t = get_minutes_played(p)

            return (p_t / all_player_time) * 100

    elif type(player) == int:
        p = Player.get(id=player)
        p_t = get_minutes_played(p)
        return (p_t / all_player_time) * 100

    elif type(player) == Player:
        p_t = get_minutes_played(Player)
        return (p_t / all_player_time) * 100


@db_session
def get_minutes_played(player,time_start=datetime.utcnow()-timedelta(days=30),time_end=datetime.utcnow()):

    if type(player) == int:
        player_index = player
        res = select(status for status in PlayerStatus if (player_index == status.player.id) and (status.time < time_end) and (status.time > time_start))

        if len(res) == 0:
            return 0
        return (len(res) * 30) / 60
    elif type(player) == str:
        if re.match(r'^STEAM_', player):
            player_steam_id = player
            res = select(status for status in PlayerStatus if (player_steam_id == status.player.steam_id) and (status.time < time_end) and (status.time > time_start))
            if len(res) == 0:
                return 0
            return (len(res) * 30) / 60
        else:
            player_name = player
            res = select(status for status in PlayerStatus if (player_name == status.player.name) and (status.time < time_end) and (status.time > time_start))
            if len(res) == 0:
                return 0
            return (len(res)*30)/60

    elif type(player) == Player:
        player_db = player
        res = select(status for status in PlayerStatus if (player_db == status.player) and (status.time < time_end) and (status.time > time_start))
        if len(res) == 0:
            return 0
        return (len(res)*30)/60

    else:
        return -9999


@db_session
def get_all_player():
    return Player.select()[0:]


@db_session
def get_maps_by_played():
    return Maps.select().order_by(desc(Maps.played))[0:]


@db_session
def create_player_status(first_saw,name,steam_id):
    if Player.exists(steam_id=steam_id):
        player = Player.get(steam_id=steam_id)
    else:
        player = Player(first_saw=first_saw, name=name, steam_id=steam_id)

    return PlayerStatus(player=player)

@db_session
def add_player(first_saw, name, steam_id):
    if Player.exists(steam_id=steam_id):
        player = Player.get(steam_id=steam_id)
        if name != player.name:
            player.name = name

        return player
    return Player(first_saw=first_saw, name=name, steam_id=steam_id)

@db_session
def get_all_server_status():
    return ServerStatus.select()[0:]

@db_session
def create_server_status_ticker(server):
    create = create_server_status(server)

    old_id = create.id-1
    if ServerStatus.exists(id=old_id):
        before = ServerStatus[old_id]
        if (before.current_map.id != create.current_map.id) and (create.human >= 2):
            before.current_map.played = before.current_map.played + 1

    return create


@db_session
def create_server_status(server):
    date = datetime.utcnow()
    bots = server.get_number_of_bots()
    human = server.get_number_of_players()
    maps = Maps.get(name=server.current_map)

    server_status = ServerStatus(date=date,
                            bots=bots,
                            human=human,
                            current_map=maps)
    return server_status

@db_session
def add_map(first_played, last_played, name):

    if Maps.exists(name=name):
        print("{} already exists".format(name))
        return Maps.get(name=name)
    try:
        mode_type = name.split('_')
        if mode_type[0] == "de":
            mode_type = "bomb"
        elif mode_type[1] == "cs":
            mode_type = "hossi"
        else:
            mode_type = "random"

        Maps(first_played=first_played, last_played=last_played,
             name=name, mode_type=mode_type)
    except:
        print("Map: {} is no proper CS-casual Map, ignore".format(name))



@db_session
def get_all_maps():
        return Maps.select()[0:]

@db_session
def get_map(ident):
    if type(ident) == str:
        return Maps.get(name=ident)
    if type(ident) == int:
        return Maps[ident]

@db_session
def print_all_server_status():
    for x in get_all_server_status():
        try:
            msg = "Bots: {} Human: {} Date: {} Map: {} Played: {}".format(x.bots,x.human,x.date,x.current_map.name,x.current_map.played)
        except Exception:
            print("Error cant print status")


@db_session
def create_test_user():
    for i in range(1000):
        add_player(datetime.utcnow(),str(i),"STEAM_1_{}".format(i))


def database_create_maps(map_list):
    dt = datetime.utcnow()
    result = []
    for m in map_list:
        result.append(add_map(dt,dt,m))

def print_all_maps():
    for x in get_all_maps():
        msg = "{} {} {}".format(x.name, x.played, x.value)




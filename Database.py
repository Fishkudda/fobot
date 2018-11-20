from pony.orm import *
from datetime import datetime

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
    value = Required(int, sql_default=True, default=1000)


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    first_saw = Required(datetime)
    steam_id = Required(str,unique=True)
    name = Required(str)
    voted = Required(int, sql_default=True, default=0)
    votes = Set('Votes')
    player_status = Set('PlayerStatus')
    multi = Required(int,sql_default=True,default=1)


class PlayerStatus(db.Entity):
    id = PrimaryKey(int, auto=True)
    time = Required(datetime,sql_default=True,default=datetime.utcnow())
    player = Required('Player')


class Votes(db.Entity):
    id = PrimaryKey(int, auto=True)
    voted = Required('Maps')
    player = Required('Player')

    @staticmethod
    def add_vote(vote,player):
        if type(vote) == str:
            map_voted= Maps.get(name=vote)
        elif type(vote) == int:
            map_voted =Maps[vote]
        else:
            map_voted = vote

        if type(player) == str:
            player_voted = Player.get(name=player)
        elif type(player) == int:
            player_voted= Player[player]
        else:
            player_voted= player

        if Votes.exists(player=player_voted,voted=map_voted):
            return Votes.get(player=player_voted,voted=map_voted)

        return Votes(voted=map_voted, player=player_voted)


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
def get_all_player():
    return Player.select()[0:]

@db_session
def get_maps_by_played():
    return Maps.select().order_by(desc(Maps.played))[0:]


@db_session
def create_player_status(first_saw,name,steam_id):
    if Player.exists(steam_id=steam_id):
        player = Player.get(steam_id=steam_id)
        print("Player: {} with steam ID {} already exists".format(player.name,
                                                                  player.steam_id))
    else:
        player = Player(first_saw=first_saw, name=name, steam_id=steam_id)

    return PlayerStatus(player=player)

@db_session
def add_player(first_saw, name, steam_id):
    if Player.exists(steam_id=steam_id):
        player = Player.get(steam_id=steam_id)
        print("Player: {} with steam ID {} already exists".format(player.name,
                                                                  player.steam_id))
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
            print(msg)
        except Exception:
            print("Error cant print status")
            print(x)

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
        print(msg)



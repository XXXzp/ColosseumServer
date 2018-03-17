# coding:utf-8
import urllib
import http.client
import requests
REFEREE_RET_EXAMPLE = {
    'status': 'success',  # Task.STATUS  and   'game no exist'
    'score': 'SCORE:47|53:a|b'  # False if game is no success
}
DEBUG_JSON = {
    'gameID': '10112323123',  # just ID number
    'game': 'dealer_renju',  # name of the game
    'NPC': 'starter',  # 'False' 'starter' 'master' 'Godlike'
    'rounds': '1000',
    'random_seed': 'False',  # 'False' 'int'
    'if_poker': 'False',  # Special in poker game
    'game_define': 'False',  # for poker game define file is required
    'players': {
        'name_1': 'Alice',
        'name_2': 'Bob'
    }
}
kwargs = {"headers": {"X-Judge-Server-Token": None}}
kwargs["json"] = DEBUG_JSON
url = 'http://0.0.0.0:8080'
p2 = requests.get(url,params=DEBUG_JSON)
p1 = requests.post(url,params=DEBUG_JSON)
print(p1.json())
#h1 = http.client.HTTPConnection('0.0.0.0/play', 8080)
#h2 = http.client.HTTPConnection('0.0.0.0/check', 8080)
#h3 = http.client.HTTPConnection('0.0.0.0/ping', 8080)



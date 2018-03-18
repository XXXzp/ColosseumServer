# coding=utf-8
import json
from .utils import get_message_from_redis, redis_init
from .task import game_task_run
DEBUG_MATCH_INFO_EXAMPLE = {
    'gameID': '10112323123',  # just ID number
    'game': 'dealer_renju',  # name of the game
    'NPC': 'starter',  # 'False' 'starter' 'master' 'Godlike'
    'rounds': '1000',
    'random_seed': 'False',  # 'False' 'int'
    'if_poker': 'False',  # Special in poker game
    'game_define': 'False',  # for poker game define file is required
    'players': [
        {'name_1': 'Alice'},
        {'name_2': 'Bob'}
    ]
}
STATUS_LIST = ['waiting', 'ongoing', 'success', 'failed']


REFEREE_RET_EXAMPLE = {
    'status': 'success',  # Task.STATUS  and   'game no exist'
    'score': 'SCORE:47|53:a|b'  # False if game is no success
}


def query_task_result(task_info):
    """
    使用查询方式，在网页上返回对局信息
    :param task_info: 同样是一个字典，必要的信息是gameID
    :return:如果游戏完成，返回得分，否则返回游戏当前的状态，score为False
    example:result = {'status': 'success', 'score': 'False'}
    """
    redis_server, pubsub = redis_init()
    pubsub.subscribe(task_info['gameID'])
    try:
        game_id = task_info['gameID']
        status_from_task = get_message_from_redis(redis_server, pubsub, game_id)
    except KeyError:
        return {
            'status': 'no exist',
            'score': 'False'
        }
    result = dict()
    if status_from_task['status'] is STATUS_LIST[2]:
        result['status'] = STATUS_LIST[2]
        result['score'] = status_from_task['score']
        pubsub.unsubscribe(game_id)
    else:
        result['score'] = 'False'
    return json.dumps(result)


def accept_task(task_info):
    """
    在Worker中接受开启游戏对局进程的请求
    在游戏对局字典中保存task实例，以备查询需求
    完成对局后返回开启的端口号字典
    :param task_info: 开启游戏，需要的信息，例子：DEBUG_JSON
    :return: example: result = {'status': 'ongoing', 'ports': { 'player1_port': '12311', 'player2_port': '12222' }}
    """
    redis_server, pubsub = redis_init()
    pubsub.subscribe(task_info['gameID'])
    game_task_run(task_info)
    status_from_task = get_message_from_redis(redis_server, pubsub, task_info['gameID'])
    pubsub.unsubscribe(task_info['gameID'])
    port = status_from_task.decode('utf-8').split()
    result = dict()
    ports = dict()
    result['status'] = 'ongoing'
    for i in range(len(port)):
        ports['player%d_port' % i] = port[i]
    result['ports'] = ports
    return json.dumps(result)

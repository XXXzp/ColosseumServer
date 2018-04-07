# coding=utf-8
import json
from .utils import get_message_from_redis, redis_init, GameStatus, logger, CONFLICT_RET
from .task import game_task_run, query_state_and_score_from_log_file


def query_task_result(task_info):
    """
    使用查询方式，在网页上返回对局信息
    :param task_info: 同样是一个字典，必要的信息是gameID
    :return:如果游戏完成，返回得分，否则返回游戏当前的状态，score为False
    example:result = {'status': 'success', 'score': 'False'}
    """
    result = dict()
    try:
        result['status'], result['score'], result['description'] = query_state_and_score_from_log_file(task_info['gameID'],task_info['game'])
    except FileNotFoundError as e:
        logger.exception(e)
        return json.dumps({
            'status': 'FILE NO FOUND OR GAME ID ERROR',
            'score': 'False',
            'description':'False'
        })
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
    if redis_server.get(task_info['gameID']):  # 防止同一GameID多次请求
        return json.dumps(CONFLICT_RET)
    ports = game_task_run(task_info)
    redis_server.set(task_info['gameID'], ports)
    result = dict()
    port_dict = dict()
    result['status'] = 'ongoing'
    for i in range(len(ports)):
        port_dict['player%d_port' % i] = ports[i]
    result['ports'] = port_dict
    return json.dumps(result)


def cleanup_db():
    pass

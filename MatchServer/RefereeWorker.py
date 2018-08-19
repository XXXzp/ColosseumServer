# coding=utf-8
import json
from .utils import redis_init, logger, CONFLICT_RET, get_pid_key, ERROR_INIT_RET, check_pid
from .task import game_task_run, query_state_and_score_from_log_file, game_process_control


def query_task_result(task_info):
    """
    使用查询方式，在网页上返回对局信息
    :param task_info: 同样是一个字典，必要的信息是gameID
    :return:如果游戏完成，返回得分，否则返回游戏当前的状态，score为False
    example:result = {'status': 'success', 'score': 'False'}
    """
    result = dict()
    try:
        result['status'], result['score'], result['description'] = \
            query_state_and_score_from_log_file(task_info['gameID'], task_info['game'])
    except FileNotFoundError as e:
        logger.exception(e)
        return json.dumps({
            'status': 'FILE NO FOUND OR GAME ID ERROR',
            'score': 'False',
            'description': 'False'
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
    redis_server = redis_init()
    game_pid_key = get_pid_key(task_info['gameID'])
    if check_pid(redis_server.get(game_pid_key)):  # 防止同一GameID多次请求
        return json.dumps(CONFLICT_RET)

    ports, pid = game_task_run(task_info)
    if not ports or not pid:
        return json.dumps(ERROR_INIT_RET)

    redis_server.set(task_info['gameID'], ports)
    redis_server.set(game_pid_key, pid)

    result = dict()
    port_dict = dict()
    result['status'] = 'ongoing'
    for i in range(len(ports)):
        if not ports[i].isdigit():
            return json.dumps(ERROR_INIT_RET)
        port_dict['player%d_port' % i] = ports[i]
    result['ports'] = port_dict
    return json.dumps(result)


def kill_by_id(task_info):
    """
    尝试对正在进行的游戏进程作操作
    :param task_info: {'game_id':'998', 'action':'terminate'}
    :return: result = {'game_id':'998',  'description':'success'}
    """
    redis_server = redis_init()
    try:
        pid = redis_server.get(get_pid_key(task_info['gameID']))
        if not pid:
            task_info['description'] = 'Process No Found'
            return json.dumps(task_info)
        action_state = game_process_control(pid, task_info['action'])
        task_info['description'] = action_state
        return json.dumps(task_info)
    except KeyError as e:
        task_info['description'] = 'Unexpected Key'
        return json.dumps(task_info)
    except Exception as e:
        print(e)
        task_info['description'] = 'Unexpected Error'
        return json.dumps(task_info)


def cleanup_db():
    pass

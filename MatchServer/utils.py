# coding=utf-8
import psutil
import socket
import os
import redis
import shutil
import logging
from .exception import MatchClientError, MatchInitError
from .configure import MATCH_LOG_FILE_BASE_DIR, GAME_DETAILS_FILE_NAME, POKER_DEFINE_FILES_DIR


logger = logging.getLogger(__name__)
handler = logging.FileHandler("log/ColosServer.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


DEBUG = True

CONFLICT_RET = {
    'status': 'ongoing',
    'ports': 'GAME EXIST ERROR'
}


ERROR_INIT_RET = {
    'status': 'error',
    'ports': 'bad request format or check if ports are available'
}


def redis_init():
    """
    开启进程池，由于每一个游戏实际使用的CPU资源并不高，所以并发量设置在了CPU核数*100
    以及一个Task队列，这个队列是保存了gameID:task的字典
    便于获取游戏的结果
    """
    redis_server = redis.StrictRedis()
    return redis_server


def get_message_from_redis(pubsub):
    for message in pubsub.listen():
        return message['data']


def get_log_path(game_id, game_type, if_init=True):
    log_path = os.path.join(MATCH_LOG_FILE_BASE_DIR, game_id, game_type + 'log_file')
    if if_init:
        return log_path
    else:
        return log_path + '.log'


def get_transaction_path(game_id, game_type, if_init=True):
    transaction_path = os.path.join(MATCH_LOG_FILE_BASE_DIR, game_id, \
                           game_type + 'transaction_file')
    if if_init:
        return transaction_path
    else:
        return transaction_path + '.log'


def get_game_detail_path(game_id):
    return os.path.join(MATCH_LOG_FILE_BASE_DIR, game_id, GAME_DETAILS_FILE_NAME)


def get_pid_key(game_id):
    return game_id + 'pid'


def get_game_define_path(game_define):
    path = os.path.join(POKER_DEFINE_FILES_DIR, game_define)
    if os.path.exists(path):
        return path
    else:
        return None


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    else:
        return True


def server_info():
    """
    利用python的几个模块完成服务器信息的获取
    :return: 返回服务器信息的字典
    """
    return {"hostname": socket.gethostname(),
            "cpu": psutil.cpu_percent(),
            "cpu_core": psutil.cpu_count(),
            "memory": psutil.virtual_memory().percent,
            }


def get_token():
    _token = os.environ.get("TOKEN")
    if _token:
        return _token
    else:
        raise MatchClientError("env 'token' not found")


# token = hashlib.sha256(get_token()).hexdigest()

def clean_tmp_dir(path):
    try:
        shutil.rmtree(path)
    except Exception as e:
        logger.exception(e)
        raise MatchInitError("failed to clean runtime dir")


class InitSubmissionEnv(object):
    """
    对每一次Match创建一个临时目录完成代码的运行
    代码上实现__enter__和__exit__方法实现便于with..as..的用法
    """
    def __init__(self, workspace, match_id):
        self.path = os.path.join(workspace, match_id)

    def __enter__(self):
        try:
            os.makedirs(self.path)
        except FileExistsError as file_exist_error:
            logger.exception(file_exist_error)
        except Exception as e:
            logger.exception(e)
            raise MatchInitError("failed to create runtime dir")
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not DEBUG:
            try:
                shutil.rmtree(self.path)
            except Exception:
                raise MatchInitError("failed to clean runtime dir")


class GameStatus:

    WAITING = 'waiting'
    ONGOING = 'ongoing'
    SUCCESS = 'success'
    TIMEOUT = 'timeout'
    FAILED = 'failed'


# coding=utf-8
import psutil
import socket
import os
import redis
import shutil
import logging
from .exception import MatchClientError, MatchInitError


logger = logging.getLogger(__name__)
handler = logging.FileHandler("log/ColosServer.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


DEBUG = True

CONFLICT_RET = {
    'status': 'ongoing',
    'ports': 'GAME EXIST ERROR',
}


def redis_init():
    """
    开启进程池，由于每一个游戏实际使用的CPU资源并不高，所以并发量设置在了CPU核数*100
    以及一个Task队列，这个队列是保存了gameID:task的字典
    便于获取游戏的结果
    """
    redis_server = redis.StrictRedis()
    pubsub = redis_server.pubsub(ignore_subscribe_messages=True)
    return redis_server, pubsub


def get_message_from_redis(pubsub):
    for message in pubsub.listen():
        return message['data']


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


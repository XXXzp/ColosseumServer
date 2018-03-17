# coding=utf-8
import psutil
import socket
import os

import shutil

from .exception import MatchClientError, MatchInitError

'''
logger = logging.getLogger(__name__)
handler = logging.FileHandler("/log/judge_server.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)
'''

DEBUG = True


def get_message_from_redis(redis_server, pubsub, channel):
    print('start listening')
    message = redis_server.get(channel)
    redis_server.delete(channel)
    if message:
        return message
    for message in pubsub.listen():
        if message['channel'] != channel:
            redis_server.set(channel, message['data'])
        else:
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


class InitSubmissionEnv(object):
    """
    对每一次Match创建一个临时目录完成代码的运行
    代码上实现__enter__和__exit__方法实现便于with..as..的用法
    """
    def __init__(self, workspace, match_id):
        self.path = os.path.join(workspace, match_id)
        print(self.path)

    def __enter__(self):
        try:
            os.makedirs(self.path)
        except FileExistsError as file_exist_error:
            print(file_exist_error)
        except Exception:
            raise MatchInitError("failed to create runtime dir")
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not DEBUG:
            try:
                shutil.rmtree(self.path)
            except Exception:
                raise MatchInitError("failed to clean runtime dir")

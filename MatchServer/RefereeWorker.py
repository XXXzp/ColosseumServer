# coding=utf-8
import json
import psutil
import subprocess
import redis
import time
from multiprocessing import Pool, Process
from .utils import InitSubmissionEnv,get_message_from_redis
from .configure import MATCH_LOG_FILE_BASE_DIR

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


class Task(Process):
    """
    完成单个对局进程
    保存对局信息
    focus on one specify task
    """

    def __init__(self, match_info):
        """
        这里主要是一个线程的Condition初始化
        :param match_info:对局信息例子见DEBUG_MATCH_INFO_EXAMPLE
        """
        Process.__init__(self)
        self.status = STATUS_LIST[0]
        self.log_path = MATCH_LOG_FILE_BASE_DIR
        self.game_id = match_info['gameID']
        self.cmd, self.log_path = self._prepare_for_work(match_info)
        self.redis_server = redis.StrictRedis()  # using default at debug stage
        self.pubsub = self.redis_server.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(self.game_id)

    def run(self):
        print('trying to create worker thread! ')
        with InitSubmissionEnv(MATCH_LOG_FILE_BASE_DIR, self.game_id) as temp_dir:
            with open(temp_dir+'/game_detail.txt', 'w+') as file:
                p = subprocess.Popen(self.cmd, shell=False, stdout=file)
                first = False
                while p.poll() is None:
                    if not first:
                        first = True
                        file_read = open(temp_dir+'/game_detail.txt', 'r+')
                        while True:
                            line = file_read.readline().strip()
                            if line != '':
                                print(line)
                                break
                            else:
                                time.sleep(0.01)
                        self.redis_server.publish(self.game_id, line)
                if p.returncode == 0:
                    self.status = STATUS_LIST[2]
                else:
                    self.status = STATUS_LIST[3]
                self.from_match_log(temp_dir)
            print('thread exiting')

    @staticmethod
    def _prepare_for_work(match_info):
        """
        完成将对局信息转化成命令行，同时返回log文件的路径避免重复计算
        :param match_info:对局信息例子见DEBUG_MATCH_INFO_EXAMPLE
        :return:命令行，路径
        """
        # shell_cmd = './dealer_renju asdddd 1000 Alice Bob'
        # cmd = shlex.split(shell_cmd)
        cmd = []
        log_path = MATCH_LOG_FILE_BASE_DIR + match_info['gameID'] + '/' + match_info['game']
        cmd.append(match_info['game'])
        cmd.append(log_path)
        if match_info['if_poker'] != 'False':
            cmd.append(match_info['game_define'])
        cmd.append(match_info['rounds'])
        if match_info['random_seed'] != 'False':
            cmd.append(match_info['random_seed'])
        players = match_info['players']
        for player in players:
            for key, val in player.items():
                cmd.append(val)
        return cmd, log_path

    def from_match_log(self, log_path):
        """
        作文件操作，从log文件读取对局得分
        :param log_path:
        :return: 对局得分String
        """
        result = 'NONE'
        if self.status is STATUS_LIST[2]:
            file = open(log_path)
            lines = file.readlines()
            result = lines[-1]
        print('from_match_log', result)
        self.redis_server.publish(self.game_id, result)


REFEREE_RET_EXAMPLE = {
    'status': 'success',  # Task.STATUS  and   'game no exist'
    'score': 'SCORE:47|53:a|b'  # False if game is no success
}


class RefereeWorker(object):
    """
    focus on task scheduling
    每个Server实例有一个Worker对象
    用于对局线程的开启
    """

    def __init__(self):
        """
        开启进程池，由于每一个游戏实际使用的CPU资源并不高，所以并发量设置在了CPU核数*100
        以及一个Task队列，这个队列是保存了gameID:task的字典
        便于获取游戏的结果
        """
        self._pool = Pool(psutil.cpu_count()*100)
        self.redis_server = redis.StrictRedis()
        self.pubsub = self.redis_server.pubsub(ignore_subscribe_messages=True)

    def start_one_match(self, task_info):
        """
        完成一次对局
        开启对局后，马上返回游戏的端口号供用户连接或者是预置AI
        :param task_info: 开启游戏，需要的信息，例子：DEBUG_JSON
        :return: 返回端口List，任务对象
        """
        task = Task(task_info)
        task.start()
        task.join()

    def query_task_result(self, task_info):
        """
        使用查询方式，在网页上返回对局信息
        :param task_info: 同样是一个字典，必要的信息是gameID
        :return:如果游戏完成，返回得分，否则返回游戏当前的状态，score为False
        example:result = {'status': 'success', 'score': 'False'}
        """
        try:
            game_id = task_info['gameID']
            self.redis_server.publish(game_id, 'get_game_status')
        except KeyError:
            return {
                'status': 'no exist',
                'score': 'False'
            }
        result = dict()
        status_from_task = get_message_from_redis(self.redis_server, self.pubsub, game_id)
        if status_from_task['status'] is STATUS_LIST[2]:
            result['status'] = STATUS_LIST[2]
            result['score'] = status_from_task['score']
            self.pubsub.unsubscribe(game_id)
        else:
            result['score'] = 'False'
        return json.dumps(result)

    def accept_task(self, task_info):
        """
        在Worker中接受开启游戏对局进程的请求
        在游戏对局字典中保存task实例，以备查询需求
        完成对局后返回开启的端口号字典
        :param task_info: 开启游戏，需要的信息，例子：DEBUG_JSON
        :return: example: result = {'status': 'ongoing', 'ports': { 'player1_port': '12311', 'player2_port': '12222' }}
        """
        self.pubsub.subscribe(task_info['gameID'])
        #self.start_one_match(task_info)
        task = Task(task_info)
        task.start()
        print('starting finished')
        #self._pool.apply_async()
        status_from_task = get_message_from_redis(self.redis_server, self.pubsub, task_info['gameID'])
        print(status_from_task)
        port = status_from_task['port'].split()
        print("Finishing start_one_match", port)
        result = dict()
        ports = dict()
        result['status'] = 'ongoing'
        for i in range(len(port)):
            ports['player%d_port' % i] = port[i]
        result['ports'] = ports
        return json.dumps(result)

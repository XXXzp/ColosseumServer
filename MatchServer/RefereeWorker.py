import psutil
import threading
import subprocess
from multiprocessing import Pool
from .utils import InitSubmissionEnv
from .configure import MATCH_LOG_FILE_BASE_DIR
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


class Task(object):
    """
    focus on one specify task
    """
    STATUS = ['waiting', 'ongoing', 'success', 'failed']

    def __init__(self):
        self.ports = []
        self.status = Task.STATUS[0]
        self.log_path = MATCH_LOG_FILE_BASE_DIR
        self.condition = threading.Condition()
        self.result = ""
        self.worker = None

    def run(self, match_info):
        """

        :param match_info:
        :return:
        """
        cmd, self.log_path = self._prepare_for_work(match_info)
        self.worker = threading.Thread(target=self.worker_thread, args=(cmd, match_info['gameID'], ))
        self.worker.run()
        self.condition.acquire()
        self.condition.wait()
        self.condition.release()
        return self.ports

    def from_match_log(self):
        if self.STATUS is Task.STATUS[2]:
            file = open(self.log_path)
            lines = file.readlines()
            self.result = lines[-1]

    @staticmethod
    def _prepare_for_work(match_info):
        """

        :param match_info:
        :return:
        """
        # shell_cmd = './dealer_renju asdddd 1000 Alice Bob'
        # cmd = shlex.split(shell_cmd)
        cmd = []
        log_path = MATCH_LOG_FILE_BASE_DIR + match_info['gameID'] + '/' + match_info['game']
        cmd.append('./' + match_info['game'])
        cmd.append(log_path)
        if match_info['if_poker']:
            cmd.append(match_info['game_define'])
        cmd.append(match_info['rounds'])
        if match_info['random_seed'] is not 'False':
            cmd.append(match_info['random_seed'])
        players = match_info['players']
        for key, val in players.items():
            cmd.append(val)
        return cmd, log_path

    def worker_thread(self, cmd, game_id):
        """

        :param cmd:
        :param game_id:
        :return:
        """
        with InitSubmissionEnv(MATCH_LOG_FILE_BASE_DIR, game_id):
            p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            first = False
            while p.poll() is None:
                line = p.stdout.readline()
                if not first:
                    first = True
                    line = line.decode('utf-8')
                    self.ports = line.strip().split()
                    self.condition.acquire()
                    self.condition.notify()
                    self.condition.release()
            if p.returncode == 0:
                self.STATUS = Task.STATUS[2]
            else:
                self.STATUS = Task.STATUS[3]
            self.from_match_log()

    def get_status(self):
        return self.STATUS


REFEREE_RET_EXAMPLE = {
    'status': 'success',  # Task.STATUS  and   'game no exist'
    'score': 'SCORE:47|53:a|b'  # False if game is no success
}


class RefereeWorker(object):
    """
    focus on task scheduling
    """

    def __init__(self):
        self._pool = Pool(psutil.cpu_count()*100)
        self.task_queue = dict()

    @staticmethod
    def __start_one_match(task_info):
            task = Task()
            port = task.run(task_info)
            return port, task

    def query_task_result(self, task_info):
        game_id = task_info['gameID']
        try:
            task = self.task_queue[game_id]
        except KeyError:
            return {
                'status': 'no exist',
                'score': 'False'
            }
        result = dict()
        result['status'] = task.get_status()
        if result['status'] is Task.STATUS[2]:
            result['score'] = task.result
            del self.task_queue[game_id]
        else:
            result['score'] = 'False'
        return result

    def accept_task(self, task_info):
        port, task = self._pool.apply_async(self.__start_one_match, args=(task_info,))
        self.task_queue[task_info['gameID']] = task
        return port

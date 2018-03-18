import time
import redis
import subprocess
from .utils import InitSubmissionEnv
from .configure import MATCH_LOG_FILE_BASE_DIR


STATUS_LIST = ['waiting', 'ongoing', 'success', 'failed']


def game_task_run(match_info):
    game_id = match_info['gameID']
    cmd, log_path = _prepare_for_work(match_info)
    redis_server = redis.StrictRedis()  # using default at debug stage
    pubsub = redis_server.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(game_id)
    with InitSubmissionEnv(MATCH_LOG_FILE_BASE_DIR, game_id) as temp_dir:
        with open(temp_dir+'/game_detail.txt', 'w+') as file:
            file.truncate()
            p = subprocess.Popen(cmd, shell=False, stdout=file, stderr=file)
            file_read = open(temp_dir+'/game_detail.txt', 'r+')
            while True:
                line = file_read.readline().strip()
                if line != '':
                    break
                else:
                    time.sleep(0.01)
            redis_server.publish(game_id, line)
            if p.returncode == 0:
                status = STATUS_LIST[2]
            else:
                status = STATUS_LIST[3]
            _from_match_log(redis_server, game_id, status, temp_dir)


def _prepare_for_work(match_info):
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


def _from_match_log(redis_server, game_id, status, log_path):
    if status is STATUS_LIST[2]:
        file = open(log_path)
        lines = file.readlines()
        result = lines[-1]
        redis_server.publish(game_id, result)

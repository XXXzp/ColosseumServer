import time
import subprocess
from .exception import MatchInitError
from .utils import InitSubmissionEnv, redis_init, GameStatus, logger
from .configure import MATCH_LOG_FILE_BASE_DIR


def game_task_run(match_info):
    game_id = match_info['gameID']
    cmd, log_path = _prepare_for_work(match_info)
    redis_server, pubsub = redis_init()
    pubsub.subscribe(game_id)
    try:
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
                p.wait()
                if p.returncode == 0:
                    status = GameStatus.SUCCESS
                else:
                    status = GameStatus.FAILED
                _from_match_log(redis_server, game_id, status, temp_dir)
    except MatchInitError as e:
        logger.exception(e)


def _prepare_for_work(match_info):
    cmd = []
    log_path = MATCH_LOG_FILE_BASE_DIR + match_info['gameID'] + '/' + match_info['game']
    cmd.append(match_info['game'])
    cmd.append(log_path)
    if match_info['game_define'] != 'False':
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
    if status is GameStatus.SUCCESS:
        try:
            file = open(log_path)
            lines = file.readlines()
            result = lines[-1]
            redis_server.set(game_id + 'FINAL_RESULT', result)
        except FileNotFoundError as e:
            logger.exception(e)
    else:
        redis_server.set(game_id + 'FINAL_RESULT', status)


def _record_match_detail(redis_server, file):
    pass

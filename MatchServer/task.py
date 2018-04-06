# coding=utf-8
import time
import subprocess
import re
from .exception import MatchInitError
from .utils import InitSubmissionEnv, redis_init, GameStatus, logger
from .configure import MATCH_LOG_FILE_BASE_DIR, GAME_DETAILS_FILE_NAME


def game_task_run(match_info):
    game_id = match_info['gameID']
    cmd, log_path = _prepare_for_work(match_info)
    try:
        with InitSubmissionEnv(MATCH_LOG_FILE_BASE_DIR, game_id) as temp_dir:
            with open(temp_dir+GAME_DETAILS_FILE_NAME, 'w+') as file:
                p = subprocess.Popen(cmd, shell=False, stdout=file, stderr=file)
                file_read = open(temp_dir+GAME_DETAILS_FILE_NAME, 'r+')
                while True:
                    line = file_read.readline().strip().split()
                    if line:
                        file_read.close()
                        break
                    else:
                        time.sleep(0.01)
                return line
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


def query_state_and_score_from_log_file(game_id):
    file = open(MATCH_LOG_FILE_BASE_DIR+game_id+'/'+GAME_DETAILS_FILE_NAME, 'r+')
    lines = file.readlines()
    if lines == '':
        return GameStatus.WAITING, "False"
    result = lines[-1]
    if re.search("MATCH",result):
        return GameStatus.ONGOING, "False"
    elif re.search("SCORE",result):
        return GameStatus.SUCCESS, result
    else:
        return GameStatus.FAILED, "False"


def _record_match_detail(redis_server, file):
    pass

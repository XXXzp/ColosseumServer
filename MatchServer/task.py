# coding=utf-8
import time
import subprocess
import re
import os
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


def query_state_and_score_from_log_file(game_id, game_name):
    with open(MATCH_LOG_FILE_BASE_DIR+game_id+'/'+game_name+'.log','r+') as file_game_log:
        game_logs = file_game_log.readlines()

        if game_logs:
            last_line_list = game_logs[-1].split(':')
        else:
            if os.path.exists(MATCH_LOG_FILE_BASE_DIR+game_id+'/'+GAME_DETAILS_FILE_NAME):
                return GameStatus.WAITING, "False", GameStatus.WAITING
            else:
                return GameStatus.WAITING, "False", 'the Game hasnt started yet'
            
        if last_line_list[0] == 'MATCH' or last_line_list[0][0]=='#':  # 或者说写死这里不太好？  注意一下！！
            # 尽管最后一行是match，仍可能是超时，或者错误
            with open(MATCH_LOG_FILE_BASE_DIR+game_id+'/'+GAME_DETAILS_FILE_NAME, 'rb+') as file_game_detail:
                timeout_flag = False
                file_game_detail.seek(-1000,2)
                for line in reversed(file_game_detail.readlines()):
                    line_decode = line.decode('utf-8')
                    if re.search("timeout",line_decode):
                        timeout_flag = True
                    elif re.search('ERROR',line_decode):
                        if  timeout_flag:
                            return GameStatus.TIMEOUT, 'False', line_decode
                        else:
                            return GameStatus.FAILED, 'False', line_decode
                    elif re.search("WARRNING",line_decode):
                        return GameStatus.ONGOING, 'False', line_decode
                    else:
                        return GameStatus.ONGOING, "False", game_logs[-1]

        elif last_line_list[0] == 'SCORE':
            # SCORE:489|511:Alice|Bob
            scores = list(map(int,last_line_list[1].split('|')))
            index = scores.index(max(scores))
            return GameStatus.SUCCESS, str(scores),last_line_list[2].split('|')[index]
        else:
            print(last_line_list)
            raise RuntimeError('Unexpected file state')


def _record_match_detail(redis_server, file):
    pass

# coding=utf-8
import subprocess
import re
import os
import time
import psutil
import datetime
from .utils import InitSubmissionEnv, GameStatus, logger, get_log_path, \
    get_transaction_path, get_game_detail_path, check_pid, get_game_define_path
from .configure import MATCH_LOG_FILE_BASE_DIR, GAME_DETAILS_FILE_NAME


def game_task_run(match_info):
    game_id = match_info['gameID']
    cmd, log_path = _prepare_for_work(match_info)
    with InitSubmissionEnv(MATCH_LOG_FILE_BASE_DIR, game_id) as temp_dir:
        detail_path = temp_dir+GAME_DETAILS_FILE_NAME
        with open(detail_path, 'w+') as file:
            p = subprocess.Popen(cmd, shell=False, stdout=file, stderr=file)
            file_read = open(detail_path, 'r+')
            while True:
                line = file_read.readline()
                if "Error:" in line:
                    return None, None
                line = line.strip().split()
                if line:
                    file_read.close()
                    break
                else:
                    time.sleep(0.01)
            return line, p.pid


def _prepare_for_work(match_info):
    try:
        cmd = list()
        log_path = get_log_path(match_info['gameID'], match_info['game'])
        transaction_path = get_transaction_path(match_info['gameID'], match_info['game'])
        cmd.append(match_info['game'])
        cmd.append(log_path)
        if match_info['game_define'] != 'False':  # poker define file
            game_define = get_game_define_path(match_info['game_define'])
            if game_define:
                cmd.append(game_define)
            else:
                return None, None
        cmd.append(match_info['rounds'])
        if match_info['random_seed'] != 'False':
            cmd.append(match_info['random_seed'])

        players = match_info['players']
        for player in players:
            cmd += list(player.values())

        if match_info['keep_transaction'] != 'False':  # check if keep transaction file
            cmd.append('-T')
            cmd.append(transaction_path)

        fixed_port_info = match_info['fixed_ports']
        if fixed_port_info['if_fixed'] != 'False':
            cmd.append('-p')
            ports = fixed_port_info['ports']
            ports_list = list()
            for port in ports:
                ports_list += port.values()
            cmd.append(','.join(ports_list))

        # time control
        cmd.append('--t_response')
        cmd.append(match_info['t_response'])
        cmd.append('--t_hand')
        cmd.append(match_info['t_hand'])
        cmd.append('--t_per_hand')
        cmd.append(match_info['t_per_hand'])
        cmd.append('--start_timeout')
        cmd.append(match_info['wait_time_out'])

        return cmd, log_path
    except KeyError as e:
        logger.exception(e)
        print('key error detected when preparing for work, check request format')
        return None, None


def game_process_control(pid, action):
    try:
        if check_pid(pid):
            process = psutil.Process(int(pid))
            if action == 'terminate':
                try:
                    process.terminal()
                    process.wait(timeout=5)
                except psutil.NoSuchProcess as e:
                    logger.exception(e)
                    return 'terminate failed:no such process'
                except psutil.TimeoutExpired as e:
                    logger.exception(e)
                    return 'terminate failed:time out'
                return 'terminate success'

            elif action == 'startTime':
                return datetime.datetime.fromtimestamp(process.create_time()).strftime("%Y-%m-%d %H:%M:%S")
            elif action == 'status':
                return process.status()
            else:
                return 'action unexpected!'
        else:
            return 'Process Not Running anymore'
    except Exception as e:
        print(e)
        return 'Unknown Error'


def query_state_and_score_from_log_file(game_id, game_name):
    with open(get_log_path(game_id, game_name, False), 'r+') as file_game_log:
        game_logs = file_game_log.readlines()

        if game_logs:
            last_line_list = game_logs[-1].strip('\n').split(':')
        else:
            # 开启游戏进程但没有玩家连接对局是没有game log的，但是存在game detail文件
            if os.path.exists(get_game_detail_path(game_id)):
                return GameStatus.WAITING, "False", GameStatus.WAITING
            else:
                return GameStatus.WAITING, "False", 'the Game hasnt started yet'
            
        if last_line_list[0] == 'MATCH' or last_line_list[0][0] == '#':  # 或者说写死这里不太好？  注意一下！！
            # 尽管最后一行是match，仍可能是超时，或者错误
            with open(get_game_detail_path(game_id), 'rb+') as file_game_detail:
                timeout_flag = False
                file_game_detail.seek(-1000, 2)
                for line in reversed(file_game_detail.readlines()):
                    line_decode = line.decode('utf-8')
                    if re.search("timeout", line_decode):
                        timeout_flag = True
                    elif re.search('ERROR', line_decode):
                        if timeout_flag:
                            return GameStatus.TIMEOUT, 'False', line_decode
                        else:
                            return GameStatus.FAILED, 'False', line_decode
                    elif re.search("WARRNING", line_decode):
                        return GameStatus.ONGOING, 'False', line_decode
                    else:
                        return GameStatus.ONGOING, "False", game_logs[-1]

        elif last_line_list[0] == 'SCORE':
            # SCORE:489|511:Alice|Bob
            scores = list(map(int, last_line_list[1].split('|')))
            index = scores.index(max(scores))
            return GameStatus.SUCCESS, str(scores), last_line_list[2].split('|')[index]
        else:
            print(last_line_list)
            raise RuntimeError('Unexpected file state')

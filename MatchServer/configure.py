# coding=utf-8
import grp  # group
import os
import pwd  # password database

MATCH_WORKSPACE_BASE = "/match_run"
LOG_BASE = "/log"
MATCH_LOG_FILE_BASE_DIR = '/tmp/Colosseum/'
POKER_DEFINE_FILES_DIR = 'poker_defines/'
GAME_DETAILS_FILE_NAME = '/game_detail.txt'

COMPILER_LOG_PATH = os.path.join(LOG_BASE, "compile.log").encode("utf-8")
MATCH_RUN_LOG_PATH = os.path.join(LOG_BASE, "match.log").encode("utf-8")

RUN_USER_UID = pwd.getpwnam("nobody").pw_uid  # 返回对应name的用户信息
RUN_GROUP_GID = grp.getgrnam("nogroup").gr_gid  # 返回对应name的组信息

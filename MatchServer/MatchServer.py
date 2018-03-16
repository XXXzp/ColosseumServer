# coding:utf-8
import json
import cgi
import re
import urllib
from http.server import BaseHTTPRequestHandler
from .utils import server_info
from .RefereeWorker import RefereeWorker

RESULT = {
    'status': 'ongoing',
    'score': 'False',
    'xxx': 12312
}


class MatchServerHandler(BaseHTTPRequestHandler):

    @staticmethod
    def send_error_info():
        return {'ret': 'ServerError',
                'data': 'Invalid'}

    @staticmethod
    def pong():
        """
        ping pong操作
        :return:返回服务信息
        """
        data = server_info()
        data["action"] = "pong"
        return data

    def do_GET(self):
        info_server = server_info()
        message = json.dumps(info_server)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(message, encoding='utf-8'))

    def do_POST(self):
        worker = self.__dict__.get('worker', None)
        if worker is None:
            worker = RefereeWorker()
        result = ""
        if re.search('/api', self.path):
            if self.headers.get_params()[0][0] == 'application/json':
                length = int(self.headers.get_params(header='Content-Length')[0][0])
                data = self.rfile.read(length)
                data = json.loads(data)
                switcher = {
                    '/play': worker.accept_task,
                    '/check': worker.query_task_result,
                    '/ping': self.pong
                }
                if re.search('/play', self.path):
                    result = worker.accept_task(data)
                elif re.search('/check', self.path):
                    result = worker.query_task_result(data)
                elif re.search('/ping', self.path):
                    result = self.pong()
                else:
                    result = self.send_error_info()
        else:
            result = json.dumps({'err': None,
                                 'data': None})

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(result, encoding='utf-8'))

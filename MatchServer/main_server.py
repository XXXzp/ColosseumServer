# coding=utf-8
import json
import web

from .RefereeWorker import RefereeWorker
from .utils import server_info

urls = (
    "/play", "RefereeServer",
    '/check', "RefereeServer",
    "/ping", "RefereeServer"
)

class RefereeServer(object):
    """
    使用web.py具体文档见
    http://webpy.org/
    完成代码执行前的准备工作
    作为服务器接受外部判题请求
    focusing on connections
    """

    def __init__(self):
        self.worker = RefereeWorker()

    def GET(self):
        json.dumps(server_info())

    def POST(self):
        """
        处理POST请求
        :return:返回结果的json
        """
        if web.data():
            try:
                data = json.loads(web.data())
            except Exception as e:
                return self.send_error()
        else:
            return json.dumps({'err': None,
                          'data': None})
        switcher = {
            '/play': self.worker.accept_task,
            '/check': self.worker.query_task_result,
            '/ping': self.pong
        }
        callback = switcher.get(web.ctx['path'], self.send_error)
        return json.dumps({'err': None,
                          'data': callback(**data)})

    @staticmethod
    def pong():
        """
        ping pong操作
        :return:返回服务信息
        """
        data = server_info()
        data["action"] = "pong"
        return data

    @staticmethod
    def send_error():
        return {'ret': 'ServerError',
                'data': 'Invalid'}

    @staticmethod
    def get_web_app():
        app = web.application(urls, globals())
        wsgiapp = app.wsgifunc()
        # gunicorn -w 4 -b 0.0.0.0:8080 server:wsgiapp
        return app, wsgiapp

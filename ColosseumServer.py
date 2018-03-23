# coding=utf-8
from MatchServer.MatchServer import MatchServerHandler
from http.server import HTTPServer
from socketserver import ForkingMixIn


class ThreadedHTTPServer(ForkingMixIn, HTTPServer):
    """
    https://pymotw.com/2/BaseHTTPServer/index.html#module-BaseHTTPServer
    py3 也类似
    """
    pass


server = ThreadedHTTPServer(('localhost', 8081), MatchServerHandler)
print('Starting server, use <Ctrl-C> to stop')
server.serve_forever()

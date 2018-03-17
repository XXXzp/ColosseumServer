from MatchServer.main_server import app,wsgiapp
from MatchServer.MatchServer import MatchServerHandler
from http.server import HTTPServer


server = HTTPServer(('0.0.0.0', 34535), MatchServerHandler)
server.serve_forever()

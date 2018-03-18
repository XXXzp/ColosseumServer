from MatchServer.MatchServer import MatchServerHandler
from http.server import HTTPServer


server = HTTPServer(('0.0.0.0', 33333), MatchServerHandler)
server.serve_forever()

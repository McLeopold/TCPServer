import logging
import json
from time import time

class NullHandler(logging.Handler):
    def emit(self, record):
        pass
    
h = NullHandler()

class Game():
    log = logging.getLogger("game")
    log.addHandler(h)
    game_info = {'player_count': 2}
    
    def __init__(self):
        self.players = {}
        self.time = time()
#        self.alive = None
#        self.waiting_on = None
#        self.time = time()
#        
#    def start(self):
#        self.alive = [x for x in range(1, Game.game_info['player_count']+1)]
#        self.waiting_on = self.alive[:]
#        self.time = time()

    def update_timeout(self):
        self.time = time()
        Game.log.debug('timeout updated to %s' % self.time)
        
    def timeout(self):
        return time() - self.time > Game.game_info['timeout']

class Player():
    log = logging.getLogger("player")
    log.addHandler(h)
    def __init__(self, sock, name, protocol=0):
        self.sock = sock
        self.name = name
        self.protocol = protocol
        #self.player_id = None
        
    def __repr__(self):
        #return 'Player(%d): %s' % (self.sock.fileno(), self.name)
        return 'Player: %s' % self.name
    
    def send(self, msg):
        Player.log.debug('Sending to player %s: %s' % (self, msg))
        if self.protocol == 0:
            self.sock.sendall(str(msg))
            if type(msg) == str and not msg.startswith('INFO'):
                self.sock.sendall('go\n')
        elif self.protocol == 1:
            self.sock.sendall(json.dumps(msg))
            
    def send_errors(self, errors):
        if self.protocol == 0:
            for error in errors:
                self.sock.sendall('INFO %s\n' % error)
        elif self.protocol == 1:
            self.sock.sendall(json.dumps({'errors': errors}) + '\n')                
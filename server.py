import tcpserver
import webserver
import threading
import signal
        
class TCPThread(threading.Thread):
    def __init__(self, game_data, game_data_lock):
        threading.Thread.__init__(self)
        self.game_data = game_data
        self.game_data_lock = game_data_lock

    def run(self):
        tcpserver.main(self.game_data, self.game_data_lock)

class WebThread(threading.Thread):
    def __init__(self, game_data, game_data_lock):
        threading.Thread.__init__(self)
        self.game_data = game_data
        self.game_data_lock = game_data_lock
        
    def run(self):
        webserver.main(self.game_data, self.game_data_lock)

if __name__ == '__main__':
    from gamedata import GameData
    game_data = GameData('PlanetWars')
    game_data_lock = threading.Lock()

    try:
        tcpthread = TCPThread(game_data, game_data_lock)
        tcpthread.start()
        webthread = WebThread(game_data, game_data_lock)
        webthread.start()
    except KeyboardInterrupt:
        pass

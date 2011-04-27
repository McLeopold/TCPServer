from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler 
import os
import re
import threading
import logging
import json

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)

# create logger
log = logging.getLogger('web')
log.setLevel(logging.DEBUG)
# add ch to logger
log.addHandler(ch)

class CacheDict(dict):
    def __init__(self, max=1):
        super(CacheDict,self).__init__()
        self.itemlist = []
        self.max = max
    def __setitem__(self, key, value):
        if key not in self.itemlist and len(self.itemlist) >= self.max:
            del_item = self.itemlist.pop(0)
            del self[del_item]
        self.itemlist.append(key)
        super(CacheDict,self).__setitem__(key, value)
    def __getitem__(self, key):
        if self.itemlist[-1] != key:
            self.itemlist.remove(key)
            self.itemlist.append(key)
        return super(CacheDict,self).__getitem__(key)
    def __iter__(self):
        return iter(self.itemlist)
    def keys(self):
        return self.itemlist
    def values(self):
        return [self[key] for key in self]  
    def itervalues(self):
        return (self[key] for key in self)

class GameServer(HTTPServer):
    def set_game_data(self, game_data, game_data_lock):
        self.game_data = game_data
        self.game_data_lock = game_data_lock
        self.game_cache = CacheDict(1000)
        self.query_cache = CacheDict(1000)
        self.html_cache = CacheDict(1000)

class GameHandler(BaseHTTPRequestHandler): #SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, *args):
        self.urls = (('\/([0-9]+)\.game', self.serve_game_file),
                     ('^\/game.*', self.serve_game_viewer),
                     ('^\/list.*', self.serve_list_viewer),
                     ('^\/?(.*)', self.serve_static_file))
        BaseHTTPRequestHandler.__init__(self, *args)
        #SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args)
        
    def serve_list_viewer(self, match):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.server.game_data_lock.acquire()
        try:
            game_list = self.server.game_data.get_game_list()
        finally:
            self.server.game_data_lock.release()
        self.wfile.write(json.dumps(game_list))        
        
    def serve_game_viewer(self, match):
        if not self.server.html_cache.has_key('game.html'):
            f = open(os.path.join('htdocs','game.html'), 'r')
            html = f.read()
            f.close()
            self.server.html_cache['game.html'] = html
        else:
            html = self.server.html_cache['game.html']
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(html)

    def serve_game_file(self, match):
        try:
            game_id = int(match.group(1))
            if self.server.game_cache.has_key(game_id):
                game_text = self.server.game_cache[game_id]
            else:
                fname = os.path.join('games', '%s.game' % match.group(1))
                f = open(fname, 'r')
                game_text = f.read()
                f.close()
                self.server.game_cache[game_id] = game_text
            self.send_response(200)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write(game_text)
        except IOError, e:
            print(e)
            self.send_error(404, 'File Not Found: %s' % self.path)

    def serve_static_file(self, match):
        fname = os.path.join('htdocs', match.group(1) or 'index.html')
        log.debug("looking for %s \ %s" % (os.getcwd(), fname))
        if os.path.exists(fname):
            f = open(fname)
            self.send_response(200)
            if fname.endswith('.js'):
                self.send_header('Content-type','text/javascript')
            elif fname.endswith('.css'):
                self.send_header('Content-type','text/css')
            elif fname.endswith('.html'):
                self.send_header('Content-type','text/html')
            else:
                self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
        else:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_GET(self):
        for regex, func in self.urls:
            match = re.search(regex, self.path)
            if match:
                func(match)
                break
        else:
            self.send_error(404, 'File Not Found: %s' % self.path)

def main(game_data, game_data_lock):
    PORT = 2080    
    httpd = GameServer(('', PORT), GameHandler)
    httpd.set_game_data(game_data, game_data_lock)
    log.info('serving at port %d' % PORT)
    httpd.serve_forever()

if __name__ == '__main__':
    from gamedata import GameData
    game_data = GameData('PlanetWars')
    game_data_lock = threading.Lock()
    main(game_data, game_data_lock)
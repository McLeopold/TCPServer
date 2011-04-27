#!/usr/bin/env python
import select
import socket
import sys
import os
import signal
import platform
from PlanetWars.PlanetWars import PlanetWars
from game import Player
from time import time
import logging
import json
import threading

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)

# create logger
log = logging.getLogger('tcp')
log.setLevel(logging.INFO)
# add ch to logger
log.addHandler(ch)

gamelog = logging.getLogger('game')
gamelog.setLevel(logging.DEBUG)
gamelog.addHandler(ch)

gamedatalog = logging.getLogger('gamedata')
gamedatalog.setLevel(logging.DEBUG)
gamedatalog.addHandler(ch)

ServerGame = PlanetWars
server_player_count = ServerGame.game_info['player_count']

BUFSIZ = 4096

from game import Game
from math import ceil, sqrt
from time import time
import json
import logging
from collections import Counter, deque, defaultdict

log = logging.getLogger("game.PlanetWars")

class TCPGame():
    def __init__(self, game):
        self.game = game
        pass
    
    def send_moves(self, player, moves):
        pass
    
    def in_progress(self):
        return True
    
    def run_game(self, botcmds, timeoutms, loadtimeoutms, num_turns=1000,
             output_file="testout.txt", verbose=False, serial=False):
        try:
            f = open('bot1.txt', 'w')
            # create bot sandboxes
            bots = [Sandbox(*bot) for bot in botcmds]
            for b, bot in enumerate(bots):
                if not bot.is_alive:
                    print('bot %s did not start' % botcmds[b])
                    self.game.kill_player(b)
    
            if output_file:
                of = open(output_file, "w")
                of.write(self.game.get_state())
                of.flush()
    
            print('running for %s turns' % num_turns)
            for turn in range(num_turns+1):
                print('turn %s' % turn)
                try:
                    if turn == 1:
                        self.game.start_game()
    
                    # send game state to each player
                    for b, bot in enumerate(bots):
                        if self.game.is_alive(b):
                            if turn == 0:
                                bot.write(self.game.get_player_start(b) + 'ready\n')
                                if b == 0:
                                    f.write(self.game.get_player_start(b))
                                    f.flush()
                            else:
                                bot.write(self.game.get_player_state(b) + 'go\n')
                                if b == 0:
                                    f.write(self.game.get_player_state(b))
                                    f.flush()
                    if turn > 0:
                        self.game.start_turn()
    
                    # get moves from each player
                    if turn == 0:
                        time_limit = float(loadtimeoutms) / 1000
                    else:
                        time_limit = float(timeoutms) / 1000
                    start_time = time.time()
                    bot_finished = [not self.game.is_alive(b) for b in range(len(bots))]
                    bot_moves = ['' for b in bots]
    
                    # loop until received all bots send moves or are dead
                    #   or when time is up
                    while (sum(bot_finished) < len(bot_finished) and
                            time.time() - start_time < time_limit):
                        for b, bot in enumerate(bots):
                            if bot_finished[b]:
                                continue # already got bot moves
                            if not bot.is_alive:
                                print('bot died')
                                bot_finished[b] = True
                                self.game.kill_player(b)
                                continue # bot is dead
                            line = bot.read_line()
                            if line is None:
                                continue
                            line = line.strip()
                            if line.lower() == 'go':
                                bot_finished[b] = True
                            else:
                                bot_moves[b] += line + '\n'
    
                    # process all moves
                    if turn > 0 and not self.game.game_over():
                        self.game.do_all_moves(bot_moves)
                        self.game.finish_turn()
    
                except:
                    traceback.print_exc()
                    print("Got an error running the bots.")
                    raise
    
                if output_file:
                    of.write(self.game.get_state())
                    of.flush()
    
                if verbose:
                    stats = self.game.get_stats()
                    s = 'turn %4d stats: '
                    for key, values in stats:
                        s += '%s: %s' % (key, values)
                    sys.stderr.write("\r%-50s" % s)
    
                alive = [self.game.is_alive(b) for b in range(len(bots))]
                #print('alive %s' % alive)
                if sum(alive) <= 1:
                    break
    
            self.game.finish_game()
            #print(game.get_state())
    
        finally:
            for bot in bots:
                if bot.is_alive:
                    bot.kill()
            if output_file:
                of.close()
        return "Game Over, %s" % self.game.get_scores()
        f.close()

class TCPGameServer(object):    
    def __init__(self, game_data, game_data_lock, port=2010, backlog=5, main_thread=False):
        self.game_data = game_data
        self.game_data_lock = game_data_lock
        
        self.clients = []
        self.clientmap = {}
        
        self.waiting = 0
        self.players_waiting = []
        log.info('game id starting at %s' % (self.game_data.last_game_id + 1))
        self.games = {}

        self.gamemap = {}

        # tcp binding options
        self.port = port
        self.backlog = backlog
        self.running = False
        self.force_shutdown = False
        self.main_thread = main_thread
        
        self.bind()
        
    def bind(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('',self.port))
        log.info('Listening to port %d ...' % self.port)
        self.server.listen(self.backlog)
        # Trap keyboard interrupts
        if self.main_thread:
            signal.signal(signal.SIGINT, self.sighandler)
        
    def sighandler(self, signum, frame):
        self.running = False
        self.force_shutdown = False
        
    def shutdown(self):
        # Close the server
        log.info('Shutting down server...')
        # Close existing client sockets
        for o in self.clients:
            o.close()
            
        self.server.close()
        
    def select_map(self):
        map_name = os.path.join('PlanetWars','boards','original','map7.txt')
        data = []
        f = open(map_name, 'r')
        for line in f:
            data.append(line)
        f.close()
        return map_name, data
        
    def select_players(self):
        # select players and remove from waiting list
        players = []
        for i in range(server_player_count):
            players.append(self.players_waiting.pop(0))
        return players
        
    def create_game(self):
        # create a new game
        game_number = self.game_data.get_next_game_id()
        game = ServerGame()
        map_name, map_data = self.select_map()
        game.parse_map_old(map_data)
        self.games[game_number] = game
        players = self.select_players()
        player_id = 0
        for player in players:
            player_id += 1
            game.players[player_id] = player
            self.gamemap[player] = (player_id, game, game_number)
        self.waiting -= server_player_count
        log.info('created game %d with map %s with players %s' % (game_number, map_name, players))
        self.send_game_state(game)
        
    def process_player_data(self, player, data):
        # process an individual player's moves for a game
        player_id, game, game_id = self.gamemap[player]
        info = game.parse_player_data(data, player.protocol)
        log.debug('parsed player data: %s' % info)
        if info.has_key('crashed') and info['crashed'] == True:
            log.info('%d reported crash' % player)
            game.kick_player(player_id)
            player.sock.shutdown(socket.SHUT_RD)
        elif info.has_key('errors') and len(info['errors']) > 0:
            log.info('kicking %d in game %d because of move parse errors' % (player_id, game_id))
            game.kick_player(player_id)
            player.send_errors(info['errors'])
            player.sock.shutdown(socket.SHUT_RD)
        else:
            errors = game.input_moves(player_id, info['moves'])
            if errors != None and len(errors) > 0:
                player.send_errors(errors)
                if ServerGame.game_info['kick_invalid']:
                    log.info('kicking %d in game %d because of an invalid move' % (player_id, game_id))
                    game.kick_player(player_id)
                    player.sock.shutdown(socket.SHUT_RD)
                
    def send_game_state(self, game):
        for player_id, player in game.players.items():
            game_state = game.get_game_state_old(player_id)
            player.send(game_state)
        log.debug('sending game state:\n\n%s\n' % game_state)
        log.debug('timeout set to %d' % ServerGame.game_info['timeout'])
        
    def send_results(self, game):
        try:
            results = game.get_results()
            for player_id, player in game.players.items():
                player.send(results)
                player.sock.close()
                self.clients.remove(player.sock)
                del self.clientmap[player.sock]
                del self.gamemap[player]
            log.debug('sending game results:\n\n%s\n' % results)
        except:
            quit()
            
    def check_games(self):
        for game_id, game in self.games.items():
            if game.ready_to_process():
                game.process_turn()
                if not game.finished():
                    self.send_game_state(game)
                    game.update_timeout()
            elif game.timeout():
                for player_id, player in game.players.items():
                    if player.sock != None and player_id in game.waiting_on:
                        log.info('kicking player %d in game %d because of timeout' % (player_id, game_id))
                        game.kick_player(player_id)
                        player.send('INFO TIMEOUT')
                        player.sock.shutdown(socket.SHUT_RD)
        remove_games = []
        for game_id, game in self.games.items():
            if game.finished():
                log.info('game %d is finished' % game_id)
                self.send_results(game)
                remove_games.append(game_id)
                try:
                    f = open(os.path.join('games','%d.game' % game_id), 'w')
                    f.write(game.get_history_string())
                    f.close
                except Exception, e:
                    log.exception(e)
                    quit()
                self.game_data_lock.acquire()
                self.game_data.save_game(game_id,
                                         game.get_results(),
                                         game.get_history_string(),
                                         {}) #p_id for p_id, p in game.players.items()})
                self.game_data_lock.release()
        for game_id in remove_games:
            log.debug("removing game %d from system" % game_id)
            del self.games[game_id]
        
    def serve(self):
        inputs = [self.server]

        self.running = True
        last_update = time()

        while self.running or (len(self.clients) > 0 and not self.force_shutdown):
            if (time() - last_update) >= 10.0:
                log.info('%d connections, %d games' % (len(self.clients), len(self.games)))
                last_update = time()
                
            try:
                self.check_games()
            except Exception, e:
                log.exception(e)
            
            try:
                inputready,outputready,exceptready = select.select([self.server] + self.clients, [], [], 0.1)
            except select.error, e:
                log.exception(e)
                break
            except socket.error, e:
                log.exception(e)
                break

            for s in inputready:

                if s == self.server:
                    # handle the server socket
                    client, address = self.server.accept()
                    self.clients.append(client)
                    log.info('tcpgameserver: got connection %d from %s' % (client.fileno(), address))
                    
                    # Read the login name
                    player_data = client.recv(4096)
                    log.debug("received data from client: %s" % (player_data))
                    
                    if type(player_data) == dict:
                        player = Player(client, **player_data)
                    elif type(player_data) == list:
                        player = Player(client, *player_data)
                    elif type(player_data) == str:
                        data = player_data.split()
                        player = Player(client, data[1])
                    self.clientmap[client] = player
                    log.debug('created player: %s' % player)

                    self.waiting += 1
                    self.players_waiting.append(player)
                    # create new game if needed
                    if self.waiting >= server_player_count:
                        self.create_game()
                    
                else:
                    # handle all other sockets
                    player = self.clientmap[s]
                    try:
                        data = s.recv(BUFSIZ)
                        if data:
                            log.debug("received data from %s:\n %s" % (player, data))
                            self.process_player_data(player, data)
                        else:
                            log.info('tcpgameserver: %d hung up' % s.fileno())
                            s.close()
                            inputs.remove(s)
                            self.outputs.remove(s)
                                
                    except socket.error, e:
                        # Remove
                        log.warning('client socket error: %s' % e)
                        if s in inputs:
                            inputs.remove(s)
                        if s in self.outputs:
                            self.outputs.remove(s)
                        if s in self.clients_waiting:
                            self.players_waiting.remove(s)
                            self.waiting -= 1
                        if s in self.gamemap:
                            game_id, game = self.gamemap[s]
                            game.kick_player(player.player_id)
                        
                        

        self.shutdown()

def main(game_data, game_data_lock, main_thread=False):
    import serveroptions
    (options, args) = serveroptions.get_options(sys.argv)
    log.debug(options)
    tcp = TCPGameServer(game_data, game_data_lock, main_thread=main_thread)
    if options.test_game:
        game = ServerGame()
        map_name, map_data = tcp.select_map()
        log.info('testing map %s' % map_name)
        game.parse_map_old(map_data)
    else:
        try:
            tcp.serve()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    from gamedata import GameData
    game_data = GameData('PlanetWars')
    game_data_lock = threading.Lock()
    main(game_data, game_data_lock, True)
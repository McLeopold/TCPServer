import os
import cPickle
import logging

# results should be a dict of player_id in game and ranking

log = logging.getLogger('gamedata')

class GameData():
    def __init__(self, game_name):
        if os.path.exists(game_name + ".results"):
            f = open(game_name + '.results','r')
            self.games = cPickle.load(f)
            f.close()
            self.results = []
            log.info('loading games: %s' % self.games.keys())
        else:
            self.games = {}
            self.results = []
        self.game_name = game_name
        if len(self.games) == 0:
            self.last_game_id = 0
        else:
            self.last_game_id = max(self.games.keys())

        if os.path.exists(game_name + '.players'):
            f = open(game_name + '.players')
            self.players = cPickle.load(f)
            f.close()
        else:
            self.players = {}

    def get_next_game_id(self):
        self.last_game_id += 1
        return self.last_game_id

    def save_player(self, player_name, player_data=None):
        self.players[player_name] = player_data
        self.persist_players()

    def save_game(self, game_id, results, game_data, players):
        self.games[game_id] = {'results': results,
                               'players': players,
                               'game_data': game_data}
        self.persist_results()

    def get_game_data(self, game_id):
        return self.games[game_id][1]

    def get_game_list(self):
        header = ['game_id', 'player_1', 'player 2', 'result']
        body = []
        for game_id in self.games.keys():
            game = self.games[game_id]
            print(game)
            body.append([game_id, game['players'][1], game['players'][2], game['results']])
        return [header, body]

    def persist_results(self):
        log.debug('persisting game data to %s' % (self.game_name + '.results'))
        f = open(self.game_name + '.results','w')
        cPickle.dump(self.games, f)
        f.close()

    def persist_players(self):
        log.debug('persisting player data to %s' % (self.game_name + '.players'))
        f = open(self.game_name + '.players', 'w')
        cPickle.dump(self.players, f)
        f.close()
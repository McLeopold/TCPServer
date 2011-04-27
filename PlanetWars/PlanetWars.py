from game import Game
from math import ceil, sqrt
from time import time
import json
import logging
from collections import Counter, deque, defaultdict

log = logging.getLogger("game.PlanetWars")

class Planet():
    def __init__(self, x, y, owner, num_ships, growth_rate):
        self.x = x
        self.y = y
        self.owner = owner
        self.num_ships = num_ships
        self.growth_rate = growth_rate
    def __repr__(self):
        return 'P %s %s %s %s %s\n' % (self.x, self.y, self.owner, self.num_ships, self.growth_rate)
    def pov_old(self, player_id):
        if self.owner == 1:
            owner = player_id
        elif self.owner == player_id:
            owner = 1
        else:
            owner = self.owner
        return 'P %s %s %s %s %s\n' % (self.x, self.y, owner, self.num_ships, self.growth_rate)

class Fleet:
    def __init__(self, owner, num_ships, source_planet, destination_planet, total_trip_length, turns_remaining):
        self.owner = owner
        self.num_ships = num_ships
        self.source_planet = source_planet
        self.destination_planet = destination_planet
        self.total_trip_length = total_trip_length
        self.turns_remaining = turns_remaining
        
    def __repr__(self):
        return 'F %s %s %s %s %s %s\n' % (self.owner, self.num_ships, self.source_planet, self.destination_planet, self.total_trip_length, self.turns_remaining)
    
    def pov_old(self, player_id):
        if self.owner == 1:
            owner = player_id
        elif self.owner == player_id:
            owner = 1
        else:
            owner = self.owner
        return 'F %s %s %s %s %s %s\n' % (owner, self.num_ships, self.source_planet, self.destination_planet, self.total_trip_length, self.turns_remaining)
               
class PlanetWars(Game):
    def __init__(self):
        Game.__init__(self)

        PlanetWars.game_info['player_count'] = 2
        PlanetWars.game_info['turn_limit'] = 200
        PlanetWars.game_info['timeout'] = 1.0
        PlanetWars.game_info['kick_invalild'] = True

        self.planets = {}
        self.distance = {}
        self.fleets = []
        self.turn = 0
        self.ship_count = []
        
        self.history = []

        self.score = {}
        
        self.alive = [x for x in range(1, PlanetWars.game_info['player_count']+1)]
        self.waiting_on = self.alive[:]
        self.time = time()

        log.debug('game initiated')
        
    def validate_moves(self, player_id, moves):
        valid_moves = []
        errors = []
        ships_from_source = defaultdict(list)
        if player_id in self.waiting_on:
            move_errors = []
            for move in moves:
                source_planet_id, destination_planet_id, num_ships = move
                if source_planet_id < 0 or source_planet_id >= len(self.planets):
                    move_errors.append("Invalid source planet: %d" % source_planet_id)
                if destination_planet_id < 0 or destination_planet_id >= len(self.planets):
                    move_errors.append("Invalid destination planet: %d" % destination_planet_id)
                if source_planet_id == destination_planet_id:
                    move_errors.append("Invalid route: %d -> %d" % (source_planet_id, destination_planet_id))
                source_planet = self.planets[source_planet_id]
                if source_planet.owner != player_id:
                    move_errors.append("Source planet not owned: %d" % source_planet_id)
                if num_ships < 0 or num_ships > source_planet.num_ships:
                    move_errors.append("Invalid ship amount: %d, %d available" % (num_ships, source_planet.num_ships))
                if num_ships > 0:
                    ships_from_source[source_planet_id].append(num_ships)
                if sum(ships_from_source[source_planet_id]) > source_planet.num_ships:
                    move_errors.append("Invalid total ship amount: %d=%d, %d available" % 
                                  ('+'.join(ships_from_source[source_planet_id]), 
                                   sum(ships_from_source[source_planet_id]), source_planet.num_ships))
                if len(move_errors) == 0:
                    valid_moves.append(move)
                else:
                    errors.extend(move_errors)
        else:
            errors.append('Already sent in moves' % player_id)
        return valid_moves, errors
    
    def input_moves(self, player_id, moves):
        log.debug('input moves for player %d: %s' % (player_id, moves))
        valid_moves, errors = self.validate_moves(player_id, moves)
        for move in valid_moves:
            distance = self.distance[(move[0], move[1])]
            fleet = Fleet(player_id, move[2], move[0], move[1], distance, distance)
            self.fleets.append(fleet)
        self.waiting_on.remove(player_id)
        return errors
    
    def ready_to_process(self):
        return len(self.waiting_on) == 0 and len(self.alive) > 0 and self.turn < PlanetWars.game_info['turn_limit']

    def finished(self):
        log.debug('alive: %s, turn: %d' % (self.alive, self.turn))
        return len(self.alive) <= 1 or self.turn >= PlanetWars.game_info['turn_limit']
        
    def kick_player(self, player_id):
        log.debug('kick player %d' % player_id)
        self.score[player_id] = self.turn
        self.alive.remove(player_id)
        self.waiting_on.remove(player_id)
        self.fleets = [fleet for fleet in self.fleets if fleet.owner != player_id]
        for planet in self.planets:
            if planet.owner == player_id:
                planet.owner = 0

    def save_turn_history(self):
        planet_history = [[p.owner, p.num_ships] for p in self.planets]
        fleet_history = [[f.owner, f.num_ships, f.source_planet, f.destination_planet, f.total_trip_length, f.turns_remaining] for f in self.fleets]
        turn_history = planet_history + fleet_history
        self.history[1].append(turn_history)
        
    def get_history_string(self):
        return '|'.join(
            [':'.join(
                [','.join(
                    [str(piece) if not type(piece) == list else '.'.join(
                        [str(atom) for atom in piece]
                    ) for piece in part]
                ) for part in section]
            ) for section in self.history]
        )
        
    def process_turn(self):
        log.debug('processing turn %d' % self.turn)
        # player may have 0 ships, but still exist if they own a planet
        exists = [False for x in range(PlanetWars.game_info['player_count']+1)]
        self.ship_count = [0 for x in range(PlanetWars.game_info['player_count']+1)]
        # departure
        for fleet in self.fleets:
            if fleet.turns_remaining == fleet.total_trip_length:
                source_planet = self.planets[fleet.source_planet]
                source_planet.num_ships -= fleet.num_ships
        # advancement
        for planet in self.planets:
            if planet.owner != 0:
                planet.num_ships += planet.growth_rate
        fleets_by_destination = defaultdict(list) # [[] for x in range(len(self.planets))]
        for fleet in self.fleets:
            fleet.turns_remaining -= 1
            if fleet.turns_remaining == 0:
                try:
                    fleets_by_destination[fleet.destination_planet].append(fleet)
                except:
                    log.error('fleets_by_destination: %s, fleet: %s' % (fleets_by_destination, fleet))
            else:
                exists[fleet.owner] = True
                self.ship_count[fleet.owner] += fleet.num_ships
        # arrival
        for destination_planet_id in range(len(self.planets)):
            destination_planet = self.planets[destination_planet_id]
            fleets = fleets_by_destination[destination_planet_id]
            if len(fleets) > 0:
                ships = [0 for x in range(PlanetWars.game_info['player_count']+1)]
                ships[destination_planet.owner] += destination_planet.num_ships
                for fleet in fleets:
                    ships[fleet.owner] += fleet.num_ships
                    self.fleets.remove(fleet)
                owner, num_ships = self.calc_battle(ships)
                if owner != None:
                    destination_planet.owner = owner
                destination_planet.num_ships = num_ships
            exists[destination_planet.owner] = True
            self.ship_count[destination_planet.owner] += destination_planet.num_ships
        # update score for dead player
        for player_id in range(1, PlanetWars.game_info['player_count']+1):
            if player_id in self.alive and not exists[player_id]:
                self.score[player_id] = self.turn
                self.alive.remove(player_id)
        # update waiting
        self.waiting_on = self.alive[:]
        self.turn += 1
        self.save_turn_history()
        
    def calc_battle(self, ships):
        log.debug('calc battle: %s' % ships)
        max_ships = max(ships)
        log.debug('largest force has %s' % max_ships)
        if ships.count(max_ships) > 1:
            log.debug('2 fleets have same size force, no change')
            return None, 0
        else:
            owner = ships.index(max_ships)
            log.debug('new owner: %s' % owner)
            ships.remove(max_ships)
            num_ships = max_ships - max(ships)
            log.debug('next highest ship amount: %s' % max(ships))
            log.debug('new ship amount: %s' % num_ships)
            if num_ships < 0:
                quit()
            return owner, num_ships
        
    def get_results(self):
        score = self.score.copy()
        for player_id in self.alive:
            score[player_id] = self.ship_count[player_id] + PlanetWars.game_info['turn_limit']
        log.debug('turning score into results: %s' % score)
        score_list = sorted(score.values(), reverse=True)
        rank = {}
        for player_id, player_score in score.items():
            rank[player_id] = score_list.index(player_score) + 1
        log.debug('returning results: %s' % rank)
        return rank
        
    def get_game_state_old(self, player_id):
        game_state = ''
        for planet in self.planets:
            game_state += planet.pov_old(player_id)
        for fleet in self.fleets:
            game_state += fleet.pov_old(player_id)
        return game_state
    
    def parse_map_old(self, map_data):
        self.planets = []
        for line in map_data:
            if line[0] == 'P':
                data = line.split()
                p = Planet(float(data[1]),
                           float(data[2]),
                           int(data[3]),
                           int(data[4]),
                           int(data[5]))
                self.planets.append(p)
        self.calc_distance()
        self.history.append([[p.x, p.y, p.owner, p.num_ships, p.growth_rate] for p in self.planets])
        self.history.append([])
        
    def parse_player_data(self, data, protocol=0):
        if protocol == 0:
            info = {'moves': [], 'errors': []}
            lines = data.splitlines()
            for line in lines:
                if line == 'go':
                    break
                elif not (line.startswith('#') or line == ''):
                    log.debug('parsing line: %s' % line)
                    try:
                        move = [int(x) for x in line.split()]
                        info['moves'].append(move)
                    except Exception, e:
                        info['errors'].append('error parsing line "%s": %s' % (line, e))
        elif protocol == 1:
            info = json.loads(data)
        return info
    
    def calc_distance(self):
        self.distance = {}
        planet_count = len(self.planets)
        for a in range(planet_count):
            for b in range(a, planet_count):
                if a == b:
                    self.distance[(a,b)] = 0
                else:
                    planet_a = self.planets[a]
                    planet_b = self.planets[b]
                    dx = planet_a.x - planet_b.x
                    dy = planet_a.y - planet_b.y
                    distance = int(ceil(sqrt(dx ** 2 + dy ** 2)))
                    self.distance[(a,b)] = distance
                    self.distance[(b,a)] = distance
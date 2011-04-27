from math import ceil, sqrt
from sys import stdout
import logging
import time

"""This module was from the python starter kit at
http://ai-contest.com/starter_packages/python_starter_package.zip"""



class Fleet:
  def __init__(self, owner, num_ships, source_planet, destination_planet, \
               total_trip_length, turns_remaining):
    self.owner = owner
    self.num_ships = num_ships
    self.source_planet = source_planet
    self.total_trip_length = total_trip_length
    self.turns_remaining = turns_remaining
    self.destination_planet = destination_planet

  def __repr__(self):
    return "F (o:%d, n:%d, s:%d, d: %d, t:%d, r:%d)" % (
      self.owner, self.num_ships, self.source_planet,
      self.destination_planet, self.total_trip_length,
      self.turns_remaining)

  def __lt__(self,other):
    return self.turns_remaining < other.turns_remaining
  def __eq__(self,other):
    return self.turns_remaining == other.turns_remaining
  def __gt__(self,other):
    return self.turns_remaining > other.turns_remaining    
  
class Planet:
  def __init__(self, planet_id, owner, num_ships, growth_rate, x, y):
    self.planet_id = planet_id
    self.owner = owner
    self.num_ships = num_ships
    self.growth_rate = growth_rate
    self.x = x
    self.y = y

  def __repr__(self):
    return "id: %d, owner: %d, ships: %d, growth: %d" % (self.planet_id,
                                                         self.owner,
                                                         self.num_ships,
                                                         self.growth_rate)

def sortFleetsByTime(fleets):
  tmp = [(f.turns_remaining, f) for f in fleets]
  tmp.sort()
  return [f for (junk,f) in tmp]


class PlanetWars:

  def __init__(self, gameState):
    self.planets = []
    self.fleets = []
    r = self.ParseGameState(gameState)
    if r != 1:
      logging.debug("error parsing game state")

  def dump_state(self, first_turn=False):
    if first_turn:
      return ":".join(["%.5f,%.5f,%d,%d,%d" %
                       (p.x, p.y, p.owner, p.num_ships,
                        p.growth_rate)
                       for p in self.planets]) + "|"
    else:
      out = []
      out.append(",".join(["%d.%d" % (p.owner, p.num_ships)
                           for p in self.planets]))
      if self.fleets:
        out.append(",")
        out.append(",".join(["%d.%d.%d.%d.%d.%d" %
                             (f.owner, f.num_ships, f.source_planet,
                              f.destination_planet, f.total_trip_length,
                              f.turns_remaining)
                             for f in self.fleets]))
      out.append(":")
      return "".join(out)

  def get_counts(self):
    counts = [0,0,0]
    rates = [0, 0, 0]    
    for p in self.planets:
      counts[p.owner] += p.num_ships
      rates[p.owner] += p.growth_rate
    for f in self.fleets:
      counts[f.owner] += f.num_ships

    return counts, rates
  

  def MyPlanets(self):
    return [p for p in self.planets if p.owner == 1]

  def NeutralPlanets(self):
    return [p for p in self.planets if p.owner == 0]

  def EnemyPlanets(self):
    return [p for p in self.planets if p.owner == 2]

  def NotMyPlanets(self):
    return [p for p in self.planets if p.owner != 1]

  def MyFleets(self):
    return [p for p in self.fleets if p.owner == 1]    

  def EnemyFleets(self):
    return [p for p in self.fleets if p.owner == 2]        

  def __repr__(self):
    s = ''
    for p in self.planets:
      s += "P %f %f %d %d %d\n" % \
       (p.x, p.y, p.owner, p.num_ships, p.growth_rate)
    for f in self.fleets:
      s += "F %d %d %d %d %d %d\n" % \
       (f.owner, f.num_ships, f.source_planet, f.destination_planet, \
        f.total_trip_length, f.turns_remaining)
    return s

  def Distance(self, source_planet, destination_planet):
    source = self.planets[source_planet]
    destination = self.planets[destination_planet]
    dx = source.x - destination.x
    dy = source.y - destination.y
    return int(ceil(sqrt(dx * dx + dy * dy)))

  def IssueOrder(self, source_planet, destination_planet, num_ships):
    stdout.write("%d %d %d\n" % \
     (source_planet, destination_planet, num_ships))
    stdout.flush()

  def IsAlive(self, player_id):
    for p in self.planets:
      if p.owner == player_id:
        return True
    for f in self.fleets:
      if f.owner == player_id:
        return True
    return False

  def ParseGameState(self, lines):
    planets = []
    fleets = []
    
    planet_id = 0

    for line in lines:
      line = line.split("#")[0] # remove comments
      tokens = line.split(" ")
      if len(tokens) == 1:
        continue
      if tokens[0] == "P":
        if len(tokens) != 6:
          return 0
        p = Planet(planet_id, # The ID of this planet
                   int(tokens[3]), # Owner
                   int(tokens[4]), # Num ships
                   int(tokens[5]), # Growth rate
                   float(tokens[1]), # X
                   float(tokens[2])) # Y
        planet_id += 1
        planets.append(p)
      elif tokens[0] == "F":
        if len(tokens) != 7:
          return 0
        f = Fleet(int(tokens[1]), # Owner
                  int(tokens[2]), # Num ships
                  int(tokens[3]), # Source
                  int(tokens[4]), # Destination
                  int(tokens[5]), # Total trip length
                  int(tokens[6])) # Turns remaining
        fleets.append(f)
      else:
        return 0
    logging.debug("fleets: %s", fleets)

    self.fleets = sortFleetsByTime(fleets)
    self.planets = planets
    return 1

  def FinishTurn(self):
    stdout.write("go\n")
    stdout.flush()



def main_loop(do_turn):
  turn = 0
  while(True):
    map_data = []
    start_time = time.time()
    turn += 1
    while True:
      current_line = raw_input()
      if len(current_line) >= 2 and current_line.startswith("go"):
        s = "\n".join(map_data)

        start_time = time.time()
        pw = PlanetWars(map_data)

        do_turn(pw, turn, start_time)
        pw.FinishTurn()
        break
      else:
        map_data.append(current_line)


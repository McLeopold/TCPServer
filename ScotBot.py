#!/usr/bin/env python
#import logging.config
#import logging
#import traceback
#
## TODO: time each round
#BOTNAME = 'ScotBot'
#log = logging.getLogger(BOTNAME)
#logHandler = logging.FileHandler(BOTNAME + '_debug.log', 'w')
#logFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#logHandler.setFormatter(logFormatter)
#log.addHandler(logHandler)
#log.setLevel(logging.DEBUG)
#
#comlog = logging.getLogger()
#comlogHandler = logging.FileHandler(BOTNAME + '_com.log', 'w')
#comlogHandler.setFormatter(logFormatter)
#comlog.addHandler(comlogHandler)
#comlog.setLevel(logging.DEBUG)
#
#replaylog = logging.getLogger()
#replayHandler = logging.FileHandler(BOTNAME + '_replay.log', 'w')
#replaylogFormatter = logging.Formatter("%(message)s")
#replayHandler.setFormatter(replaylogFormatter)
#replaylog.addHandler(replayHandler)
#replaylog.setLevel(logging.DEBUG)

from PlanetWars.PlanetWars_Starter import PlanetWars

# create network map
#    primary and secondary routes
#    ships should travel through network to ensure ability to redirect
# maximize growth rate
#    calculate future planet ownership and growth rates
#    calculate fleet size potential
# defense
#    calculate incoming fleets and send support
# finish
#    target enemy when growth rate is far above his

def DoTurn(pw):
    my_planets = []
    neutral_planets = []
    enemy_planets = []
    not_my_planets = []
    for planet in pw._planets:
        if planet.Owner() == 1:
            my_planets.append(planet)
        else:
            not_my_planets.append(planet)
            if planet.Owner() == 2:
                enemy_planets.append(planet)
            else:
                neutral_planets.append(planet)
    my_fleets = []
    enemy_fleets = []
    for fleet in pw._fleets:
        if fleet.Owner() == 1:
            my_fleets.append(fleet)
        else:
            enemy_fleets.append(fleet)
    # find best planet to conquer
    #log.debug("looking for best planets")
    best_investment = 0
    best_planets = []
    for planet in not_my_planets:
        investment = 1.0 * planet._growth_rate / (1 + planet._num_ships)
        if investment > best_investment:
            # check for incoming fleet
            #log.debug("checking planet for incoming fleet")
            target_planet = True
            for fleet in my_fleets:
                #log.debug("checking fleet {0}".format(fleet._owner))
                if fleet._destination_planet == planet._planet_id:
                    target_planet = False
                    break
            if target_planet:
                best_investment = investment
                best_planets.insert(0,planet)
                #log.info('found planet {0}, growth: {1} num_ships: {2} roi:{3}'.format(planet._planet_id,planet._growth_rate,planet._num_ships,investment))
    for best_planet in best_planets:
        # send fleet from closest planet
        #log.debug("finding closest planet with enough ships")
        closest_distance = 1000
        closest_planet = None
        closest_fleet_size = 0
        for planet in my_planets:
            fleet_size = best_planet.NumShips() + 2
            fleet_dist = pw.Distance(planet._planet_id, best_planet._planet_id)
            if best_planet._owner == 2:
                fleet_size += best_planet._growth_rate * (fleet_dist + 1)
            if planet._num_ships > fleet_size and fleet_dist < closest_distance:
                closest_distance = fleet_dist
                closest_planet = planet
                closest_fleet_size = fleet_size
        # check for correct number of ships
        if closest_planet:
            #log.info("Issuing Order {0}, {1}, {2}".format(closest_planet._planet_id, best_planet._planet_id, closest_fleet_size))
            pw.IssueOrder(closest_planet._planet_id, best_planet._planet_id, closest_fleet_size)
            closest_planet._num_ships -= closest_fleet_size
        #else:
        #    log.info("Not Issuing Order for planet {0}".format(best_planet._planet_id))
    
def main():
    #log.info("starting ScotBot")
    map_data = ''
    round_num = 0
    while(True):
        current_line = raw_input()
        if len(current_line) >= 2 and current_line.startswith("go"):
            pw = PlanetWars(map_data)
            try:
                round_num += 1
                #log.info("Round {0}".format(round_num))
                DoTurn(pw)
            except:
                #log.error("Unexpected error in DoTurn: {0}".format(traceback.format_exc()))
                raise
            pw.FinishTurn()
            map_data = ''
        else:
            map_data += current_line + '\n'


if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        main()
    except KeyboardInterrupt:
        print 'ctrl-c, leaving ...'
    except EOFError:
        pass
    #except:
    #    log.error("Unexpected error: {0}".format(traceback.format_exc()))

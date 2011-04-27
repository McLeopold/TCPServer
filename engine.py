#!/usr/bin/env python

import subprocess
import shlex

import threading
import Queue
import sys

from Queue import Queue, Empty
from subprocess import Popen
from threading import Thread


import PlanetWars


class BotThread(Thread):
    """
    Class to run a bot in a thread.

    Starts up a thread to talk to a bot process, and provide an
    interface to call it. Handles the timeout here.
    """
    def __init__(self, command):
        Thread.__init__(self)
        
        self.input = Queue()
        self.output = Queue()
        args = shlex.split(command)
        self.process = None
        print(args)
        self.process = Popen(args,
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        self.daemon = False
        self.start()

    def run_step(self, game_state, timeoutms):
        """Run one step of the game state."""
        self.input.put(game_state)
        try:
            
            result = self.output.get(True, timeoutms/1000.0)
            return result, True
        except Empty:
            return "TIMEOUT", False
        except Crashed:
            return "CRASHED", False


    def __del__(self):
        """Clean up the process if it is still running"""
        if self.process and self.process.poll() is None:
            self.process.kill()

    def stop(self):
        try:
            self.input.put(None)
            self.process.stdin.close()
            if self.process.poll() is None:
                self.process.kill()
        except:
            print "got an exception trying to end the bot"
            
        

    def run(self):
        """Run the bot loop.  Use run_step for individual steps"""
        try:
            if self.process.poll() is not None:
                raise Exception("bot did not start")
            while True:
                command = self.input.get(True)
                try:
                    if command is None:
                        self.process.kill()
                        break
                    # not sure if this is excesive poll()'ing... 
                    if self.process.poll() is not None:
                        self.output.put("CRASHED")
                        break
                    self.process.stdin.write(command)
                    result = []
                    while True:
                        if self.process.poll() is not None:
                            print "process crashed"
                            self.output.put("CRASHED")
                            return
                        line = self.process.stdout.readline()
                        if line is None:
                            self.output.put("CRASHED")
                            return
                        result.append(line)
                        if line.startswith("go"): break
                    self.output.put("".join(result))
                except:
                    self.output("CRASHED WITH EXCEPTION")
        except:
            pass
        

class EngineThread(Thread):
    """
    Class to run a bot in an engine.

    Need another level of threads to wait for the bot result.

    """
    def __init__(self, bot):
        Thread.__init__(self)
        self.bot = bot
        self.input = Queue()
        self.output = Queue()        
        self.event = threading.Event()
        self.daemon = False
        self.start()
        self.result = None
        
    def run(self):
        try:
            while True:
                x = self.input.get(True)
                if x is None: break
                command, timeout = x
                result = self.bot.run_step(command, timeout)
                self.output.put(result)
        except:
            pass
        
    def send_input(self, game_state, timeoutms):
        self.result = None
        self.input.put((game_state, timeoutms))


    
    def wait(self, timeoutms):
        if self.result is None:
            result = self.output.get(timeoutms/1000.0)
            if result:
                self.result = result
            else:
                self.result = ("TIMEOUTWAIT", False)
        return self.result
    


    def stop(self):
        self.input.put(None)
        self.bot.stop()
        
        
def output_game_state(pw, flip_owner):
    result = []
    for p in pw.planets:
        o = p.owner
        if flip_owner and o > 0:
            o = 3 - o
        result.append("P %f %f %d %d %d" % 
                      (p.x, p.y, o, p.num_ships, p.growth_rate))
    for f in pw.fleets:
        o = f.owner
        if flip_owner:
            o = 3 - o
        result.append("F %d %d %d %d %d %d" %
                      (o, f.num_ships,
                       f.source_planet, f.destination_planet,
                       f.total_trip_length, f.turns_remaining))
    result.append("go\n")
    return "\n".join(result)


def resolve(counts,owner):
    """Resolve a battle

    counts is a list of the number of ships from each player (neutral,
    self, enemy), and owner is the current owner of the planet.

    Returns the number of ships and owner after the battle."""
    if counts[0] < counts[1]:
        a,b = 0,1
    else:
        a,b = 1,0
    if counts[b] < counts[2]:
        c = 2
    elif counts[2] < counts[a]:
        b,c = a,b
    else:
        b,c = 2,b
    d = counts[c] - counts[b]
    if d == 0:
        return owner, 0
    else:
        return c, d


def game_step(initial_pw, p1_orders, p2_orders):
    p1_error = None
    p2_error = None
    
    def create_fleets(player, orders):
        result = []
        for line in orders.split("\n"):
            if line.startswith("go"):
                break
            src, dst, num = [int(x) for x in line.split()]
            if src == dst:
                return ([], "Invalid Move: Sent from %d to itself" % src)
            if src < 0 or src >= len(initial_pw.planets):
                return ([], "Invalid source planet: %d" % src)
            if dst < 0 or dst >= len(initial_pw.planets):
                return ([], "Invalid destination planet: %d" % dst)
            src_planet = initial_pw.planets[src]
            if src_planet.owner != player:
                return ([], "Player does not own source planet %d" % src)
            if num < 0:
                return ([], "Cannot send negative number of ships")
            if num >  src_planet.num_ships:
                return ([], "Sent too many ships from %d.  Sent %d, only %d available" %
                        (src, num, src_planet.num_ships))
            if num > 0:
                dist = initial_pw.Distance(src, dst)
                result.append(PlanetWars.Fleet(player, num, src, dst, dist, dist))
                src_planet.num_ships -= num
        return (result, None)

    # Send out new fleets
    p1_fleets, p1_error = create_fleets(1, p1_orders)
    p2_fleets, p2_error = create_fleets(2, p2_orders)

    if p1_error or p2_error:
        return initial_pw, p1_error, p2_error

    initial_pw.fleets.extend(p1_fleets)
    initial_pw.fleets.extend(p2_fleets)    

    # Grow planets
    for planet in initial_pw.planets:
        if planet.owner > 0:
            planet.num_ships += planet.growth_rate

    # Decrement fleet numbers
    for fleet in initial_pw.fleets:
        fleet.turns_remaining -= 1

    # Battle
    arriving_counts = [[0,0,0] for p in initial_pw.planets]
    for fleet in initial_pw.fleets:
        if fleet.turns_remaining == 0:
            dst,owner,num = (fleet.destination_planet,
                             fleet.owner,
                             fleet.num_ships)
            arriving_counts[dst][owner] += num
    
    for planet, counts in zip(initial_pw.planets, arriving_counts):
        if sum(counts) > 0:
            counts[planet.owner] += planet.num_ships
            owner, num = resolve(counts, planet.owner)
            planet.owner = owner
            planet.num_ships = num
    initial_pw.fleets = [fleet for fleet in initial_pw.fleets 
                         if fleet.turns_remaining > 0]

    return initial_pw, None, None


def run_game(pw, bot_one, bot_two, timeoutms, num_turns=200, 
             output_file="testout.txt", verbose=False, serial=False):
    try:
        if output_file:
            of = open(output_file, "w")
            of.write(pw.dump_state(first_turn=True))
            of.flush()


        for turn in xrange(1, num_turns+1):
            # get the moves from each player
            # if both crash, draw.  if one crashes, it loses

            try:
                timeout = timeoutms
                if turn == 1:
                    timeout *= 3
                bot_one.send_input(output_game_state(pw, False), timeout)
                if serial:
                    bot_one.wait(timeoutms)
                bot_two.send_input(output_game_state(pw, True), timeout)

                try:
                    moves_one, ok_one = bot_one.wait(timeout)
                except:
                    moves_one, ok_one = "EXCEPT", False

                try:
                    moves_two, ok_two = bot_two.wait(timeout)
                except:
                    moves_two, ok_two = "EXCEPT", False
            except:
                print "Got an error running the bots."
                raise

            if not (ok_one or ok_two):
                return "Draw! p1: %s, p2: %s" % (moves_one, moves_two)
            if not ok_one:
                return "Player 2 Wins  (p1: %s)" % moves_one
            if not ok_two:
                return "Player 1 Wins  (p2: %s)" % moves_two

            # update the game state        
            pw, p1_error, p2_error = game_step(pw, moves_one, moves_two)

            if output_file:
                of.write(pw.dump_state(False))
                of.flush()

            if (p1_error and p2_error):
                return "Draw! p1: %s, p2: %s" % (p1_error, p2_error)
            if p1_error:
                return "Player 2 Wins  (p1: %s)" % p1_error
            if p2_error:
                return "Player 1 Wins  (p2: %s)" % p2_error

            counts = [0,0,0]
            rates = [0,0,0]
            for p in pw.planets:
                counts[p.owner] += p.num_ships
                rates[p.owner] += p.growth_rate
            for f in pw.fleets:
                counts[f.owner] += f.num_ships

            if verbose:
                s = ("turn %3d counts: [%4s, %4s] rates: [%3s, %3s] count diff: %5d"
                     % (turn,
                        counts[1], counts[2], rates[1], rates[2],
                        counts[1] - counts[2]))

                sys.stderr.write("\r%-50s" % s)

            # check if they made bad moves
            p1_alive = pw.IsAlive(1)
            p2_alive = pw.IsAlive(2)        

            if not (p1_alive or p2_alive):
                return "Draw! : both out of ships"
            if not p1_alive:
                return "Player 2 Wins in %d turns" % turn
            if not p2_alive:
                return "Player 1 Wins in %d turns" % turn


        if counts[1] == counts[2]:
            return "Draw! in %d moves" % turn
        elif counts[1] > counts[2]:
            return "Player 1 Wins in %d turns (%d to %d)" % (turn, counts[1],
                                                             counts[2])
        elif counts[2] > counts[1]:
            return "Player 2 Wins in %d turns (%d to %d)" % (turn, counts[2],
                                                             counts[1])
        else:
            raise "This should never happen"

    finally:
        if output_file:
            of.close()
            

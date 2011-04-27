#!/usr/bin/env python
import time
import sys
import threading
import re
import random

from socket import socket, AF_INET, SOCK_STREAM

from engine import BotThread
from PlanetWars.PlanetWars_old import PlanetWars

class FailedToConnect(Exception): pass

def tcp(host, port, user, bot_command, options):
    # Start up the bot.  This may fail.
    bot = BotThread(bot_command)
    if not bot.is_alive():
        raise Exception("bot failed to start")
    
    of = None
    if options.output_prefix:
        of = open(options.output_prefix + '.txt','w')
    else:
        of = sys.stdout
        
    info_lines = []
    try:
        
        # Start up the network connection
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((host, port))
        if sock:
            sys.stderr.write("connected\n")
        else:
            raise FailedToConnect

        if options.password is not None:
            sock.send("USER %s PASS %s\n" % (user, options.password))
        else:
            sock.send("USER %s\n" % user)

        fp = sock.makefile()

        # play the game
        game_state = []
        need_newline = False
        line_feed = False
        turn = 0
        while True:
            if not fp: break
            line = fp.readline()
            if not line:
                break
            if line.startswith("INFO "):
                if line_feed: sys.stderr.write("\n\n")
                sys.stderr.write(line[5:].strip() + '\n')
                line_feed = False                
                if of is None:
                    info_lines.append(line.strip())
                else:
                    if need_newline:
                        of.write("\n")
                    of.write(line + "\n")
                    need_newline = False

                key = "INFO This is game_id="
                if options.output_prefix and of is None:
                    m = re.search(key + "(\\d+)", line)
                    if m:
                        game_id = m.groups()[0]
                        of = open(options.output_prefix + "." + game_id, "w")
                        for line in info_lines:
                            of.write(line + "\n")

            else:
                #print "got line: <%s>" % (line.strip())
                game_state.append(line)
                if line.startswith("go"):
                    turn += 1
                    timeoutms = 5000
                    pw = PlanetWars(game_state)
                    if of:
                        of.write(pw.dump_state(turn==1))
                        need_newline = True
                    if options.verbose:
                        counts, rates = pw.get_counts()
                        
                        s = ("turn %3d counts: [%4s, %4s] rates: [%3s, %3s] count diff: %5d"
                             % (turn,
                                counts[1], counts[2], rates[1], rates[2],
                                counts[1] - counts[2]))
                        line_feed = True
                        sys.stderr.write("\r%-50s" % s)
                    move, success = bot.run_step("".join(game_state),
                                                 timeoutms)
                    game_state = []
                    if success:
                        sock.send(move)
                    else:
                        sys.stderr.write('error ' + move + '\n')
                        break
                    
            if not sock:
                break
        bot.stop()
        bot.join()

    except FailedToConnect:
        print "failed to connect"
    except:
        print "caught exception"
        raise
    finally:
        bot.stop()
        bot.join()
        if of:
            of.close()

        
def main(argv):
    from optparse import OptionParser
    usage = """usage: %prog [options] IP PORT USERNAME BOT_COMMAND
    
    run the bot from BOT_COMMAND over the tcp connection.
    If BOT_COMMAND contains arguments, it must be quoted."""

    # The quoting in the bot command could be fixed by changing the
    # BotThread class in engine.py.  Right now, it uses shell=True.
    # If that were false, everything would be different.
    
    
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--output", dest="output_prefix",
                      help="prefix of output file  OUTPUT.game_id")    
    parser.add_option("--pass", dest="password",
                      default=None)
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true")


    parser.add_option("--num_games", dest="num_games",
                      type="int",
                      default=1)
    parser.add_option("--min_wait", dest="min_wait",
                      type="int",
                      default = 15)
    parser.add_option("--max_wait", dest="max_wait",
                      type="int",
                      default = 45)
    

    
    (options, args) = parser.parse_args()
    if len(args) < 4:
        print "not enough arguments."
        parser.print_usage()

    ip = args[0]
    
    port = int(args[1])
    user = args[2]
    command = args[3]

    count = 0
    max_wait = max(options.min_wait, options.max_wait) + 1
    min_wait = min(options.min_wait, options.max_wait)
    while True:
        tcp(ip, port, user, command, options)
        count += 1
        if count >= options.num_games: break
        wait = random.randrange(min_wait, max_wait)
        print
        print "played %d of %d games" % (count, options.num_games)
        print "time is now: %s, waiting %d seconds" % (time.asctime(), wait)
        time.sleep(wait)
        print "sleeping 2 more seconds..."
        time.sleep(2)
        
                      


if __name__ == "__main__":
    main(sys.argv[1:])

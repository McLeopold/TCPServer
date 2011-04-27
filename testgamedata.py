'''
Created on Jan 3, 2011

@author: Scott
'''
import unittest
from gamedata import GameData
import random

class Test(unittest.TestCase):

    def setUp(self):
        self.names = {1: 'Scott',
                      2: 'Bob',
                      3: 'Abel',
                      4: 'Boaz',
                      5: 'Caleb',
                      6: 'Dan',
                      7: 'Ephrium',
                      8: 'Frank' }

    def tearDown(self):
        pass

    def testSaveData(self):
        g = GameData('PlanetWars')
        g_id = g.get_next_game_id()
        result = {}
        if random.randint(0,1) == 0:
            result = {1: 1, 2: 2}
        else:
            result = {2: 1, 1: 2}
        player1 = random.randint(1,8)
        player2 = random.randint(1,8)
        g.save_game(g_id, result, 'bla', {player1: self.names[player1],
                                          player2: self.names[player2]})

    def testLoadData(self):
        g = GameData('PlanetWars')
        print()
        print("last_game_id: %s" % g.last_game_id)
        print(g.games)
        print(g.results)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLoadData']
    unittest.main()
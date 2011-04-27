from optparse import OptionParser

def get_options(args):
    parser = OptionParser()
    parser.add_option("--test-game", dest="test_game",
                      action="store_true", default=False,
                      help="test the creation of a game instance")
    return parser.parse_args(args)
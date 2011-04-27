import logging

log = None

def create_log():
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # add formatter to ch
    ch.setFormatter(formatter)
    
    # create logger
    global log
    log = logging.getLogger('tcp')
    log.setLevel(logging.INFO)
    # add ch to logger
    log.addHandler(ch)
    
    gamelog = logging.getLogger('game')
    gamelog.setLevel(logging.DEBUG)
    gamelog.addHandler(ch)
    
def get_log():
    if log == None:
        create_log()
    return log
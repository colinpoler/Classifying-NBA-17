import numpy as np
import os
import re

# Use this class to store a game
class Game:
    def __init__(self, game_code):
        self.game_code = game_code
        self.quarters = {1: Quarter(), 2: Quarter(), 3: Quarter(), 4: Quarter()}
        self.players = None
        self.teams = None
        self.misc = {}

# Use this class to store a quarter
class Quarter:
    def __init__(self):
        self.events = None
        self.shots = None
        self.possessions = None

# Use this class to store a player
class Player:
    def __init__(self):
        pass

# Load games from disk into memory
def load_processed_data(processed_dir, n=None):
    result = {}
    i = 0
    for filename in os.listdir(processed_dir):
        game_code = filename.split('.')[0]
        if n and i >= n:
            break
        if re.fullmatch('\d+', game_code) is None:
            continue
        result[game_code] = np.load(os.path.join(processed_dir, filename)).item()
        
        i += 1
    return result
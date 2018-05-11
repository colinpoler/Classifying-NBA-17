import numpy as np
import enum
import possession

# Use this type to store the type of a shot
class ShotTypes(enum.IntEnum):
    DUNK        = 1 << 0
    LAYUP       = 1 << 1
    HOOK_SHOT   = 1 << 2
    JUMP_SHOT   = 1 << 3
    
    REVERSE     = 1 << 4
    TURNAROUND  = 1 << 5
    FINGER_ROLL = 1 << 6
    STEP_BACK   = 1 << 7
    FADE_AWAY   = 1 << 8
    PULL_UP     = 1 << 9
    EVASIVE = REVERSE + TURNAROUND + FINGER_ROLL + STEP_BACK + FADE_AWAY + PULL_UP
    
    RUNNING     = 1 << 10
    DRIVING     = 1 << 11
    CUTTING     = 1 << 12
    FLOATING    = 1 << 13
    MOVING = RUNNING + DRIVING + CUTTING + FLOATING
    
    TIP         = 1 << 14
    PUTBACK     = 1 << 15
    ALLEY_OOP   = 1 << 16
    CLOSE_IN = TIP + PUTBACK + ALLEY_OOP
    
    BANK        = 1 << 17

# Classify a shot based on a string description
def classify_shot(shot_name):
    result = 0
    
    if 'Dunk' in shot_name:
        result += ShotTypes.DUNK
    if 'Layup' in shot_name:
        result += ShotTypes.LAYUP
    if 'Hook Shot' in shot_name:
        result += ShotTypes.HOOK_SHOT
    if 'Jump Shot' in shot_name or 'Bank Shot' in shot_name:
        result += ShotTypes.JUMP_SHOT
    
    if 'Reverse' in shot_name:
        result += ShotTypes.REVERSE
    if 'Turnaround' in shot_name:
        result += ShotTypes.TURNAROUND
    if 'Finger Roll' in shot_name:
        result += ShotTypes.FINGER_ROLL
    if 'Step Back' in shot_name:
        result += ShotTypes.STEP_BACK
    if 'Fade Away' in shot_name:
        result += ShotTypes.FADE_AWAY
    if 'Pull Up' in shot_name or 'Pull-Up' in shot_name:
        result += ShotTypes.PULL_UP
    
    if 'Running' in shot_name:
        result += ShotTypes.RUNNING
    if 'Driving' in shot_name:
        result += ShotTypes.DRIVING
    if 'Cutting' in shot_name:
        result += ShotTypes.CUTTING
    if 'Floating' in shot_name:
        result += ShotTypes.FLOATING
    
    if 'Tip' in shot_name:
        result += ShotTypes.TIP
    if 'Putback' in shot_name:
        result += ShotTypes.PUTBACK
    if 'Alley Oop' in shot_name:
        result += ShotTypes.ALLEY_OOP
    if 'Bank' in shot_name:
        result += ShotTypes.BANK
    
    valid_words = ['Dunk', 'Layup', 'Hook', 'Jump', 'Bank', 'Reverse', 'Turnaround', 'Finger', 'Roll', 'Step', 'Back', 'Fade', 'Away', 'Pull', 'Up', 'Running', 'Driving', 'Cutting', 'Floating', 'Tip', 'Putback', 'Alley', 'Oop', 'Shot', 'Pull-Up']
    words = shot_name.split(' ')
    for word in words:
        if word not in valid_words:
            print('Shot type not found: {}'.format(shot_name))
    
    return result

# ESQ metrix from http://www.sloansportsconference.com/wp-content/uploads/2014/02/2014-SSAC-Quantifying-Shot-Quality-in-the-NBA.pdf
ESQ_MAP = np.matrix(
   [[51.0, 41.7, 43.5, 46.9, 51.4, 54.6, 56.6, 58.8, 60.1, 60.8],
    [53.9, 41.0, 41.8, 45.8, 50.8, 53.8, 57.6, 60.8, 63.6, 61.1],
    [49.3, 34.7, 33.8, 37.3, 39.2, 41.6, 43.0, 44.3, 46.7, 44.7],
    [37.9, 32.5, 34.0, 37.4, 39.4, 43.2, 43.9, 45.9, 47.5, 46.0],
    [33.3, 32.2, 35.4, 40.4, 41.3, 43.9, 43.9, 46.4, 45.1, 44.6],
    [30.6, 32.1, 33.8, 39.3, 42.0, 44.9, 48.1, 49.6, 52.9, 54.3],
    [36.2, 34.2, 36.1, 37.9, 41.5, 41.5, 44.5, 49.5, 52.5, 46.3],
    [31.6, 34.0, 35.6, 38.1, 42.8, 44.1, 44.1, 41.8, 40.4, 51.7],
    [36.6, 34.3, 37.1, 40.7, 44.0, 51.1, 47.3, 54.0, 52.4, 53.8],
    [38.1, 39.5, 43.2, 47.6, 50.6, 51.6, 55.6, 54.9, 63.9, 57.9],
    [44.7, 45.1, 52.3, 58.8, 63.4, 72.5, 79.0, 82.8, 86.2, 78.7],
    [49.9, 52.0, 61.1, 70.4, 80.6, 83.7, 89.6, 87.1, 96.6, 96.2],
    [52.4, 54.2, 63.1, 71.1, 78.4, 82.4, 84.3, 90.2, 90.9, 100.0]]
)

ESQ_MAP_DRIBBLE = np.matrix(
   [[33.3, 38.1, 34.1, 44.7, 45.6, 54.9, 52.3, 51.6, 52.7, 57.6],
    [51.3, 35.6, 31.9, 40.1, 42.7, 47.9, 52.7, 54.3, 52.2, 47.6],
    [45.2, 33.9, 31.7, 34.8, 38.0, 37.9, 41.7, 41.9, 44.4, 44.6],
    [39.8, 31.2, 33.4, 37.1, 39.1, 44.2, 42.8, 47.6, 49.1, 47.6],
    [29.5, 29.7, 35.4, 39.5, 41.5, 42.5, 44.7, 49.1, 43.3, 42.0],
    [30.8, 31.2, 33.5, 39.5, 43.5, 46.3, 50.6, 49.4, 56.8, 66.2],
    [33.0, 34.8, 35.3, 37.0, 41.8, 41.8, 49.2, 44.8, 55.3, 40.0],
    [32.7, 34.2, 35.6, 37.7, 41.7, 43.1, 40.8, 35.1, 55.6, 60.0],
    [37.7, 34.4, 36.8, 40.5, 43.7, 50.0, 45.2, 56.9, 55.6, 54.5],
    [37.9, 38.6, 42.1, 46.7, 50.7, 48.6, 54.8, 54.4, 54.5, 60.0],
    [42.7, 43.3, 50.4, 56.7, 62.0, 71.8, 77.6, 77.3, 80.0, 84.0],
    [49.6, 48.5, 56.7, 66.4, 77.7, 80.7, 82.9, 82.1, 96.7, 93.8],
    [46.5, 49.4, 57.2, 65.4, 71.4, 76.2, 79.3, 84.6, 88.0, 100]]
)

ESQ_MAP_CATCH = np.matrix(
   [[66.7, 44.1, 53.1, 48.4, 54.6, 54.6, 57.6, 60.7, 61.7, 61.3],
    [57.6, 45.1, 47.3, 48.6, 54.0, 55.4, 58.4, 62.2, 65.6, 63.3],
    [52.9, 37.3, 38.0, 41.9, 40.9, 44.7, 43.9, 45.6, 48.0, 43.9],
    [38.1, 36.9, 36.2, 38.8, 40.1, 42.2, 44.8, 45.5, 46.0, 46.5],
    [50.0, 38.7, 35.8, 43.6, 41.0, 45.3, 43.4, 45.1, 46.8, 46.8],
    [37.5, 38.7, 35.6, 38.7, 40.2, 43.6, 47.1, 50.5, 48.4, 43.9],
    [55.0, 33.9, 41.8, 39.9, 41.3, 40.8, 42.1, 56.4, 49.0, 45.8],
    [28.8, 32.1, 38.0, 38.4, 45.5, 46.5, 47.4, 52.1, 36.0, 45.5],
    [35.5, 34.1, 40.5, 42.5, 42.9, 53.7, 51.3, 55.0, 42.1, 54.5],
    [41.0, 43.8, 48.6, 51.0, 54.6, 59.3, 60.6, 57.9, 80.0, 63.6],
    [52.3, 51.3, 59.4, 66.2, 68.5, 76.7, 84.2, 89.5, 94.9, 78.9],
    [50.4, 57.0, 68.0, 77.1, 86.3, 88.6, 94.2, 92.4, 97.1, 98.5],
    [53.8, 57.6, 68.5, 78.2, 85.2, 87.9, 85.5, 95.4, 92.6, 100]]
)

class Shot:
    def __init__(self, event, position, description, shooter):
        self.event = event
        self.position = position
        self.classification = classify_shot(description)
        self.shooter = shooter
    
    # Compute shot quality based on the dribbles, defender distance and shot distance
    def calculate_shot_quality(self, num_dribbles, defender_dist, shot_dist):
        defender_dist_index = max(min(9,int(defender_dist)),0)
    
        shot_dist_index = max(min(12,12-int(shot_dist/2.)),0)

        esq_map = ESQ_MAP
        if num_dribbles > 0:
            esq_map = ESQ_MAP_DRIBBLE
        else:
            esq_map = ESQ_MAP_CATCH

        self.quality = esq_map[shot_dist_index, defender_dist_index]
        
        return self.quality
import numpy as np
import enum

# Use this type to classify the type of action that a player might take
class PlayTypes(enum.IntEnum):
    FREE_THROW_MADE = 1
    FREE_THROW_MISSED = 2
    FIELD_GOAL_MADE = 3
    FIELD_GOAL_MISSED = 4
    OFFENSIVE_REBOUND = 5
    DEFENSIVE_REBOUND = 6
    TURNOVER = 7
    FOUL = 8
    SUBSTITUTION = 10
    TIMEOUT = 11
    JUMP_BALL = 12
    START_PERIOD = 14
    END_PERIOD = 15
    END_OF_GAME = 19
    DRIBBLE = 21
    THROW_PASS = 22
    RECEIVE_PASS = 23
    SHOT_CLOCK_VIOLATION = 28

class Possession:
    def __init__(self, game_code, quarter, team_id):
        self.game_code = game_code
        self.quarter = quarter
        self.team_id = team_id
    
    # Read a possession to make it analyzable
    def make_thread(self, events, players, verbose=False):
        self.thread = []
        
        # For every event in the possession
        state = 'awaiting start'
        for j in range(len(events)):
            # Identify the player, and their position
            player_id = events[j]['event player id']
            shot_clock = events[j]['shot clock']
            try:
                player = players[player_id]
            except KeyError:
                player = None
            if verbose:
                print("Event {} ({})".format(events[j]['event type'], events[j]['shot clock']))
            
            # If this is the start, add it to the thread regardless
            # If the shot clock hasn't changed, reset the possession because it was a timeout
            if len(self.thread) == 0:
                new_hold = Hold(shot_clock, player)
                self.thread = [new_hold]
                state = 'player holding ball'
                if verbose:
                    print("{}: start possession".format(state))
            elif self.thread[-1].start_shot_clock - shot_clock < 0 and shot_clock > 20:
                # Someone else intercepted
                prev_hold = self.thread[-1]
                prev_hold.duration = self.thread[-1].start_shot_clock - shot_clock
                prev_hold.end_type = 'intercepted'
                state = 'intercepted'
                if verbose:
                    print("{}: intercepted".format(state))
                break
            
            # If there's a foul, the possession ends
            if events[j]['event type'] == PlayTypes.FOUL or \
               events[j]['event type'] == PlayTypes.FREE_THROW_MADE or \
               events[j]['event type'] == PlayTypes.FREE_THROW_MISSED:
                prev_hold = self.thread[-1]
                prev_hold.duration = self.thread[-1].start_shot_clock - shot_clock
                prev_hold.end_type = 'foul'
                state = 'dead ball'
                if verbose:
                    print("{}: foul".format(state))
                break
            elif events[j]['event type'] == PlayTypes.SHOT_CLOCK_VIOLATION:
                prev_hold = self.thread[-1]
                prev_hold.duration = self.thread[-1].start_shot_clock - shot_clock
                prev_hold.end_type = 'shot clock violation'
                state = 'dead ball'
                if verbose:
                    print("{}: shot clock violation".format(state))
            
            # If the player is holding the ball, and starts to dribble, end the hold
            if   state == 'player holding ball' and \
                 events[j]['event type'] == PlayTypes.DRIBBLE:
                prev_hold = self.thread[-1]
                prev_hold.duration = self.thread[-1].start_shot_clock - shot_clock
                prev_hold.end_type = 'dribble'
                state = 'player dribbling ball'
                if verbose:
                    print("{}: start dribble".format(state))
            # If the player stops dribbling, make a new hold
            elif state == 'player dribbling ball' and \
                 events[j]['event type'] != PlayTypes.DRIBBLE:
                new_hold = Hold(shot_clock, player)
                self.thread.append(new_hold)
                state = 'player holding ball'
                if verbose:
                    print("{}: stop dribble".format(state))
            
            # If the player receives the ball, add a new thread item
            if   state == 'ball between players' and \
                 (events[j]['event type'] == PlayTypes.RECEIVE_PASS or \
                  events[j]['event type'] == PlayTypes.OFFENSIVE_REBOUND):
                new_hold = Hold(shot_clock, player)
                self.thread.append(new_hold)
                state = 'player holding ball'
                if verbose:
                    print("{}: receive".format(state))
            # If the player got rid of the ball, wrap up the previous thread item
            elif state == 'player holding ball' and \
                (events[j]['event type'] == PlayTypes.THROW_PASS):
                prev_hold = self.thread[-1]
                prev_hold.duration = self.thread[-1].start_shot_clock - shot_clock
                prev_hold.end_type = 'pass'
                state = 'ball between players'
                if verbose:
                    print("{}: pass".format(state))
            elif state == 'player holding ball' and \
                 (events[j]['event type'] == PlayTypes.FIELD_GOAL_MADE or \
                  events[j]['event type'] == PlayTypes.FIELD_GOAL_MISSED):
                prev_hold = self.thread[-1]
                prev_hold.duration = self.thread[-1].start_shot_clock - shot_clock
                prev_hold.end_type = 'shot'
                state = 'ball between players'
                if verbose:
                    print("{}: shot".format(state))
        
        # If someone was still holding the ball, wrap up
        if state == 'player holding ball':
            prev_hold = self.thread[-1]
            prev_hold.duration = self.thread[-1].start_shot_clock - shot_clock
            if events[-1]['event type'] == PlayTypes.SHOT_CLOCK_VIOLATION:
                prev_hold.end_type = 'shot clock violation'
            elif events[-1]['event type'] == PlayTypes.FOUL or \
                 events[-1]['event type'] == PlayTypes.FREE_THROW_MADE or \
                 events[-1]['event type'] == PlayTypes.FREE_THROW_MISSED:
                prev_hold.end_type = 'foul'
            elif events[-1]['event type'] == PlayTypes.RECEIVE_PASS:
                prev_hold.end_type = 'pass'
            elif events[-1]['event type'] == PlayTypes.OFFENSIVE_REBOUND or \
                 events[-1]['event type'] == PlayTypes.DEFENSIVE_REBOUND:
                prev_hold.end_type = 'shot'
            elif events[-1]['event type'] == PlayTypes.TURNOVER:
                prev_hold.end_type = 'turnover'
            elif events[-1]['event type'] == PlayTypes.END_PERIOD or \
                 events[-1]['event type'] == PlayTypes.END_OF_GAME:
                prev_hold.end_type = 'end period'
            else:
                prev_hold.end_type = 'unknown'
                print("Unknown end type: {} (game {} quarter {} time {})".format(
                    events[-1]['event type'],
                    self.game_code,
                    self.quarter,
                    events[-1]['game clock']))

# Use this class to store a 'hold' by a player
class Hold():
    def __init__(self, start_shot_clock=None, player=None, duration=None, end_type=None):
        self.start_shot_clock = start_shot_clock
        self.player = player
        self.duration = duration
        self.end_type = end_type
import numpy as np
import enum
import xml.etree.ElementTree as ElementTree
import os
import csv
import re
from shot import Shot
import unicodedata
import ftplib
from game import Game, Quarter
from possession import Possession, PlayTypes

# Download game files from the secondspectrum FTP server
def download_game_files(game_codes):
    # Login to the server
    ftp = ftplib.FTP()
    ftp.connect('sseupload.attcenter.com')
    ftp.login(user='????????', passwd='????????')

    # For each game code, download the below files
    for game_code in game_codes:
        filename_templates = [
            'NBA_FINAL_ONCOURT${}.XML',
            'NBA_FINAL_SEQUENCE_PBP_OPTICAL${}.XML',
            'NBA_FINALBOX_OPTICAL${}.XML',
            'NBA_FINALPBP_EXP${}.XML',
        ]
        for filename_template in filename_templates:
            filename = filename_template.format(game_code)
            print("Downloading {}".format(filename))
            ftp.retrbinary('RETR {}'.format(filename),
                           open(os.path.join('secondspectrum', filename), 'wb').write)

    ftp.quit()

# Read all the game codes from the game_codes file
def read_game_codes():
    game_codes = []
    with open('secondspectrum/game_codes.txt', 'rt') as file:
        for line in file:
            game_code = re.match('\d+', line)[0]
            game_codes.append(game_code)
    return game_codes

# Process the XMl files to produce more useable numpy arrays
def process_secondspectrum_games(secondspectrum_dir, result_dir):
    # Build a list of game codes that are actually downloaded
    game_codes = []
    for filename in os.listdir(secondspectrum_dir):
        if filename.startswith("NBA_FINAL_ONCOURT$") and filename.endswith(".XML"):
            game_code = filename.replace("NBA_FINAL_ONCOURT$", "").replace(".XML", "")
            game_codes.append(game_code)
    
    number_processed = 0
    for game_code in game_codes:
        game = Game(game_code)
        
        # Get the player data for this game
        players_data = read_player_data(
            secondspectrum_dir,
            game_code)
        game.players = players_data
        
        # Get the teams data for this game
        teams_data = read_teams_data(
            secondspectrum_dir,
            game_code)
        game.teams = teams_data
        
        for quarter in range(1,5):
            game.quarters[quarter] = Quarter()
            
            # Get the events data for this quarter
            try:
                events_data = read_pbp_data(
                    secondspectrum_dir,
                    game_code,
                    quarter,
                    teams_data,
                    players_data)
            except StopIteration:
                continue
            game.quarters[quarter].events = events_data
            
            # Get the shots data for this quarter
            shots_data = read_shots(
                secondspectrum_dir,
                game_code,
                quarter,
                players_data,
                events_data)
            game.quarters[quarter].shots = shots_data
            
            # Get the possessions data for this quarter
            possessions_data = read_possessions_data(
                secondspectrum_dir,
                game_code,
                quarter,
                players_data,
                events_data,
                shots_data)
            game.quarters[quarter].possessions = possessions_data
            
        np.save(os.path.join(result_dir, '{}.npy'.format(game_code)), game)
        
        number_processed += 1
        print("{}/{}".format(number_processed, len(game_codes)))

def read_pbp_data(dirname, game_code, quarter, teams_data, players_data):
    # Read the play-by-play document
    pbp_filename = 'NBA_FINAL_SEQUENCE_PBP_OPTICAL${}.XML'.format(game_code)
    document = ElementTree.parse(os.path.join(dirname, pbp_filename))

    sports_statistics = document.getroot()
    sports_boxscores = next(c for c in sports_statistics if c.tag == 'sports-boxscores')
    nba_boxscores = next(c for c in sports_boxscores if c.tag == 'nba-boxscores')
    nba_boxscore = next(c for c in nba_boxscores if c.tag == 'nba-boxscore')
    moments = next(c for c in nba_boxscore
                   if c.tag == 'sequence-pbp' and c.attrib['period'] == '{}'.format(quarter))
    
    # Compile all the data into a numpy table
    events_result_structure = [('shot clock', 'float'), ('game clock', 'float'),
                               ('event player id', 'int'), ('event team id', 'int'),
                               ('event type', 'int')]
    events_result = np.zeros(len(moments), dtype=events_result_structure)
    
    # For every moment in the file
    i = 0
    for moment in moments:
        # Read the data from the moment
        event_time = float(moment.attrib['game-clock'])
        event_type = int(moment.attrib['event-id'])
        event_player = int(moment.attrib['global-player-id'])
        shot_clock = float(moment.attrib['shot-clock']) if len(moment.attrib['shot-clock']) > 0 else 0

        # Record the event
        events_result[i]['game clock'] = event_time
        events_result[i]['shot clock'] = shot_clock
        events_result[i]['event player id'] = event_player
        events_result[i]['event type'] = event_type
        if event_player in players_data:
            events_result[i]['event team id'] = players_data[event_player]['team id']
        else:
            print("Unidentified player {}".format(event_player))
            events_result[i]['event team id'] = 0
        i += 1
    # Remove excess rows
    events_result.resize((i,))
    
    return events_result

def read_player_data(dirname, game_code):
    players_result = {}
    
    # Read the oncourt document
    oncourt_filename = 'NBA_FINAL_ONCOURT${}.XML'.format(game_code)
    document = ElementTree.parse(os.path.join(dirname, oncourt_filename))
    sports_statistics = document.getroot()
    sports_oncourt = next(c for c in sports_statistics if c.tag == 'sports-oncourt')
    nba_oncourt = next(c for c in sports_oncourt if c.tag == 'nba-oncourt')
    nba_oncourt_players = next(c for c in nba_oncourt if c.tag == 'nba-oncourt-players')
    
    visiting_team = next(c for c in nba_oncourt_players if c.tag == 'visiting-team')
    away_id = next(c for c in visiting_team if c.tag == 'team-code').attrib['global-id']
    
    home_team = next(c for c in nba_oncourt_players if c.tag == 'home-team')
    home_id = next(c for c in visiting_team if c.tag == 'team-code').attrib['global-id']

    # Find the name of the players in this game
    temp_players = []
    for oncourt in [c for c in nba_oncourt_players if c.tag == 'oncourt']:
        teams = [(next(c for c in oncourt if c.tag == 'visiting-team-players'), away_id),
                 (next(c for c in oncourt if c.tag == 'home-team-players'), home_id)]
        for team, team_id in teams:
            for player in team:
                name = strip_accents(player.attrib['display-name'].replace('.', ''))
                player_id = int(player.attrib['global-id'])
                temp_players.append((name, player_id, team_id))

    # Add every referenced player from the CSV file
    csv_rows = []
    with open('players.csv', 'rt') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for ordered_row in csv_reader:
            row = dict(ordered_row)
            csv_rows.append(row)
    
    # Reorganize the players data to fit into the data from the players file
    for name, player_id, team_id in temp_players:
        scores = [score_name_similarity(name, csv_row['name']) for csv_row in csv_rows]
        best_score = max(scores)
        if best_score == 0:
            print('{} not found'.format(name))
        best_score_index = scores.index(best_score)
        best_score_row = csv_rows[best_score_index]
        players_result[player_id] = best_score_row
        players_result[player_id]['team id'] = team_id
    
    return players_result

# Remove accents from a string
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def read_possessions_data(dirname, game_code, quarter, players_data, events_data, shots_data):
    # Read the box document
    box_filename = 'NBA_FINALBOX_OPTICAL${}.XML'.format(game_code)
    document_box = ElementTree.parse(os.path.join(dirname, box_filename))
    sports_statistics_box = document_box.getroot()
    sports_boxscores = next(c for c in sports_statistics_box if c.tag == 'sports-boxscores')
    nba_boxscores = next(c for c in sports_boxscores if c.tag == 'nba-boxscores')
    nba_boxscore = next(c for c in nba_boxscores if c.tag == 'nba-boxscore')
    possessions = next(c for c in nba_boxscore if c.tag == 'possessions')
    quarter_el = next(c for c in possessions
                      if c.tag == 'quarter' and int(c.attrib['number']) == quarter)
    
    possessions_result = []
    
    # For each possession, record start and end time
    # then make a processeable thread for it, and record all the shots
    for possession_el in [c for c in quarter_el if c.tag == 'possession']:
        new_possession = Possession(game_code, quarter, int(possession_el.attrib['team-global-id']))
        
        start_time = float(possession_el.attrib['time-start'].split(':')[0])*60 + \
                     float(possession_el.attrib['time-start'].split(':')[1])
        end_time = float(possession_el.attrib['time-end'].split(':')[0])*60 + \
                   float(possession_el.attrib['time-end'].split(':')[1])
        
        new_possession.events_raw = events_data[np.logical_and(
            start_time > events_data['game clock'],
            events_data['game clock'] > end_time)]
        new_possession.make_thread(new_possession.events_raw, players_data)
        
        new_possession.shots = []
        for shot in shots_data:
            if shot.event in new_possession.events_raw:
                new_possession.shots.append(shot)
                
        possessions_result.append(new_possession)
    return possessions_result

def read_teams_data(dirname, game_code):
    teams_result = {}
    
    # Read the oncourt document
    oncourt_filename = 'NBA_FINAL_ONCOURT${}.XML'.format(game_code)
    document = ElementTree.parse(os.path.join(dirname, oncourt_filename))
    sports_statistics = document.getroot()
    sports_oncourt = next(c for c in sports_statistics if c.tag == 'sports-oncourt')
    nba_oncourt = next(c for c in sports_oncourt if c.tag == 'nba-oncourt')
    nba_oncourt_players = next(c for c in nba_oncourt if c.tag == 'nba-oncourt-players')

    # Find the home team
    home_team_tag = next(c for c in nba_oncourt_players if c.tag == 'home-team')
    home_team_city = next(c for c in home_team_tag if c.tag == 'team-city').attrib['city']
    home_team_name = next(c for c in home_team_tag if c.tag == 'team-name').attrib['name']
    home_team_id = next(c for c in home_team_tag if c.tag == 'team-code').attrib['global-id']
    teams_result['home'] = {'name': home_team_name,
                            'city': home_team_city,
                            'id': home_team_id}

    # Find the away team
    away_team_tag = next(c for c in nba_oncourt_players if c.tag == 'visiting-team')
    away_team_city = next(c for c in away_team_tag if c.tag == 'team-city').attrib['city']
    away_team_name = next(c for c in away_team_tag if c.tag == 'team-name').attrib['name']
    away_team_id = next(c for c in away_team_tag if c.tag == 'team-code').attrib['global-id']
    teams_result['away'] = {'name': away_team_name,
                            'city': away_team_city,
                            'id': away_team_id}
    
    return teams_result

# Score how similar two names are, to deal with inexact matches
def score_name_similarity(a, b):
    a_split = a.split(' ')
    b_split = b.split(' ')
    result = 0
    for word in a_split:
        if word in b_split:
            result += 1
    return result

def read_shots(dirname, game_code, quarter, players_data, events_data):
    # Read the pbp document
    pbp_filename = 'NBA_FINALPBP_EXP${}.XML'.format(game_code)
    document = ElementTree.parse(os.path.join(dirname, pbp_filename))
    sports_statistics = document.getroot()
    sports_scores = next(c for c in sports_statistics if c.tag == 'sports-scores')
    nba_scores = next(c for c in sports_scores if c.tag == 'nba-scores')
    nba_pbp = next(c for c in nba_scores if c.tag == 'nba-playbyplay')
    
    # Read the box document
    box_filename = 'NBA_FINALBOX_OPTICAL${}.XML'.format(game_code)
    document_box = ElementTree.parse(os.path.join(dirname, box_filename))
    sports_statistics_box = document_box.getroot()
    sports_boxscores = next(c for c in sports_statistics_box if c.tag == 'sports-boxscores')
    nba_boxscores = next(c for c in sports_boxscores if c.tag == 'nba-boxscores')
    nba_boxscore = next(c for c in nba_boxscores if c.tag == 'nba-boxscore')
    
    # Compile all the data
    shots_result = []

    # For every play in the file
    for play in [c for c in nba_pbp if c.tag == 'play']:
        # Only look at the requested quarter
        if int(play.attrib['quarter']) != quarter:
            continue
        
        # Only look at shots
        event_id = int(play.attrib['event-id'])
        if event_id != PlayTypes.FIELD_GOAL_MADE and event_id != PlayTypes.FIELD_GOAL_MISSED:
            continue
        
        # Compute the time and link to the events
        time = float(play.attrib['time-minutes'])*60 + float(play.attrib['time-seconds'])
        event_index = np.argmin(np.abs(events_data['game clock'] - time))
        event = events_data[event_index]
        
        # Cross reference to find the shot in the shots file
        best_shot_from_file = None
        best_shot_from_file_dist = 100000000.0
        for players_team in [c for c in nba_boxscore if c.tag == 'players']:
            for player in [c for c in players_team if c.tag == 'player']:
                try:
                    shot_log = next(c for c in player if c.tag == 'shot-log')
                except StopIteration:
                    continue
                for shot_from_file in [c for c in shot_log if c.tag == 'shot']:
                    shot_from_file_time = float(shot_from_file.attrib['game-clock'].split(':')[0])*60 + float(shot_from_file.attrib['game-clock'].split(':')[1])
                    shot_from_file_dist = abs(time - shot_from_file_time)
                    if shot_from_file_dist < best_shot_from_file_dist:
                        best_shot_from_file_dist = shot_from_file_dist
                        best_shot_from_file = shot_from_file
        if best_shot_from_file is None:
            print("Can't find shot for event at time {}".format(events_data['game clock']))
            continue
        dribbles = int(best_shot_from_file.attrib['dribbles'])
        defender_dist = float(next(c for c in best_shot_from_file
                                   if c.tag == 'closest-defender').attrib['defender-distance'])
        if len(best_shot_from_file.attrib['x-coordinate']) > 0 and \
           len(best_shot_from_file.attrib['y-coordinate']) > 0:
            position = [float(best_shot_from_file.attrib['x-coordinate']),
                        float(best_shot_from_file.attrib['y-coordinate'])]
        else:
            position = [float('nan'), float('nan')]
        if len(best_shot_from_file.attrib['shot-distance']):
            shot_dist = float(best_shot_from_file.attrib['shot-distance'])
        else:
            shot_dist = 10000
        
        # Record the shot details
        description = play.attrib['detail-description']
        shooter_id = int(play.attrib['global-player-id-1'])
        shooter = players_data[shooter_id]
        new_shot = Shot(event, position, description, shooter)
        new_shot.result = 1 if best_shot_from_file.attrib['result'] == 'made' else 0
        new_shot.points = int(best_shot_from_file.attrib['points-type'])
        
        # Compute shot quality
        new_shot.calculate_shot_quality(dribbles, defender_dist, shot_dist)
        
        shots_result.append(new_shot)
    return shots_result

# Make a command line interface
if __name__ == '__main__':
    print("This program can download and process secondspectrum data")
    
    while True:
        print("Which games should I download?")
        print("(\'5\' to download game 5, \'5:10\' to download games 5 to 9, \'all\' to download all games, or <enter> to skip)")
        download_response = input('> ')

        game_codes = read_game_codes()
        if download_response == "":
            break
        elif download_response == "all":
            download_game_files(game_codes)
        elif re.match('^(\d+):(\d+)$', download_response):
            start_index = int(re.match('^(\d+):(\d+)$', download_response).group(1))
            end_index = int(re.match('^(\d+):(\d+)$', download_response).group(2))
            download_game_files(game_codes[start_index:end_index])
            break
        elif re.match('^(\d+)$', download_response):
            index = int(re.match('^(\d+)$', download_response).group(1))
            download_game_files(game_codes[index])
            break
        else:
            print("I didn't understand that.")
    
    while True:
        print("Should I process the data?")
        print("(y to process, n to skip)")
        process_response = input('> ')

        if process_response == "y":
            process_secondspectrum_games('secondspectrum', 'processed_data')
            break
        elif process_response == "n":
            break
        else:
            print("I didn't understand that.")
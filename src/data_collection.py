import requests
import json
import os
import pandas as pd
import sklearn
import time
import csv

API_KEY = "" # Used Franz's key, expires April 2025

def games_data():
    URL = f"https://api.sportradar.us/nfl/official/trial/v7/en/games/2024/REG/schedule.json?api_key={API_KEY}"
    response = requests.get(URL)

    if response.status_code == 200:
        data = response.json()
        with open('games.json', 'w') as f:
            json.dump(data, f, indent=4)
    else:
        print(f"Error {response.status_code}: {response.text}")


def team_ids():
    URL = f"https://api.sportradar.com/nfl/official/trial/v7/en/league/teams.json?api_key={API_KEY}"
    
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        with open('team_ids.txt', 'a') as f:
            for team in data["teams"]:
                f.write(f"{team['id']} {team['name']}\n")

    else:
        print(f"Error {response.status_code}: {response.text}")


def team_stats():

    with open('team_stats/team_ids.txt', 'r') as ids_file:
        team_ids = ids_file.readlines()
        
        for team_id in team_ids:
            id, name = team_id.split(' ')[0], team_id.split(' ')[1].strip()
            
            print("Working on", name)
            
            URL = f"https://api.sportradar.com/nfl/official/trial/v7/en/seasons/2024/REG/teams/{id}/statistics.json?api_key={API_KEY}"
            response = requests.get(URL)
            time.sleep(1)
            
            if response.status_code == 200:
                data = response.json()
                with open(f"team_stats/{name}.txt", 'a') as f:
                    json.dump(data, f, indent=4)
            else:
                print(f"Error {response.status_code}: {response.text}")

def create_WL_ratios():
    
    WL_ratios = dict()
       
    with open("w_l.txt", 'r') as f:
        for team in f.readlines():
            name, ratio = team.split(' ')[0], team.split(' ')[1].strip()
            WL_ratios[name] = float(ratio)
    
    with open("winloss.json", 'w') as WL_file:
        json.dump(WL_ratios, WL_file, indent=4)
        
        
def create_combined_data():
    
    combined_data = dict()
    
    for teamfile in os.listdir("team_seasonal_stats"):
        with open(f"team_seasonal_stats/{teamfile}", 'r') as readfile:
            
            data = json.load(readfile)
            
            team = teamfile.replace(".json", "")
            
            combined_data[team] = dict()
            
            combined_data[team]["touchdowns_pass"] = data["record"]["touchdowns"]["pass"]
            combined_data[team]["touchdowns_rush"] = data["record"]["touchdowns"]["rush"]
            combined_data[team]["touchdowns_total"] = data["record"]["touchdowns"]["total"]
            
            combined_data[team]["rushing_avg_yards"] = data["record"]["rushing"]["avg_yards"]
            combined_data[team]["rushing_attempts"] = data["record"]["rushing"]["attempts"]
            combined_data[team]["rushing_yards"] = data["record"]["rushing"]["yards"]

            combined_data[team]["receiving_receptions"] = data["record"]["receiving"]["receptions"]
            combined_data[team]["receiving_avg_yards"] = data["record"]["receiving"]["avg_yards"]
            combined_data[team]["receiving_yards"] = data["record"]["receiving"]["yards"]
            
            combined_data[team]["punts_attempts"] = data["record"]["punts"]["attempts"]
            combined_data[team]["punts_avg_net_yards"] = data["record"]["punts"]["avg_net_yards"]

            combined_data[team]["punt_returns_avg_yards"] = data["record"]["punt_returns"]["avg_yards"]

            combined_data[team]["penalties"] = data["record"]["penalties"]["penalties"]
            
            combined_data[team]["passing_attempts"] = data["record"]["passing"]["attempts"]
            combined_data[team]["passing_completions"] = data["record"]["passing"]["completions"]
            combined_data[team]["passing_interceptions"] = data["record"]["passing"]["interceptions"]
            combined_data[team]["passing_avg_yards"] = data["record"]["passing"]["avg_yards"]
            combined_data[team]["passing_poor_throws"] = data["record"]["passing"]["poor_throws"]
            combined_data[team]["passing_defended_passes"] = data["record"]["passing"]["defended_passes"]
            
            combined_data[team]["kickoffs_return_yards"] = data["record"]["kickoffs"]["return_yards"]

            combined_data[team]["kick_returns_avg_yards"] = data["record"]["kick_returns"]["avg_yards"]
            combined_data[team]["kick_returns_touchdowns"] = data["record"]["kick_returns"]["touchdowns"]

            combined_data[team]["interceptions"] = data["record"]["interceptions"]["interceptions"]

            combined_data[team]["int_returns_avg_yards"] = data["record"]["int_returns"]["avg_yards"]

            combined_data[team]["fumbles"] = data["record"]["fumbles"]["fumbles"]

            combined_data[team]["field_goals_attempts"] = data["record"]["field_goals"]["attempts"]
            combined_data[team]["field_goals_made"] = data["record"]["field_goals"]["made"]
            combined_data[team]["field_goals_avg_yards"] = data["record"]["field_goals"]["avg_yards"]

            combined_data[team]["defense_tackles"] = data["record"]["defense"]["tackles"]
            combined_data[team]["defense_assists"] = data["record"]["defense"]["assists"]
            combined_data[team]["defense_qb_hits"] = data["record"]["defense"]["qb_hits"]

    with open("combined_data.json", 'w') as writefile:
        json.dump(combined_data, writefile, indent=4)


def create_matchup_csv():
    
    matchups = list()
    
    with open("combined_data.json", "r") as readfile_combined_data:
        team_stats = json.load(readfile_combined_data)
    
    with open("winloss.json", "r") as readfile_winloss:
        winloss_data = json.load(readfile_winloss)
        
    teams = sorted(team_stats.keys())
    
    for i in range(len(teams)):        
        for j in range(i + 1, len(teams)):
            team_a, team_b = teams[i], teams[j]
            stats_a, stats_b = team_stats[team_a], team_stats[team_b]
            
            # Do not implement absolute values in interest of keeping directionality of team differences
            feature_diff = {f"{key}_diff": round(stats_a[key] - stats_b[key], 3) for key in stats_a} 
            
            # For convenience only - do not include when training/testing
            feature_diff["matchup"] = f"{team_a} vs {team_b}"
            
            # Target: Team A wins (1) or loses (0)
            feature_diff["outcome"] = 1 if (winloss_data[team_a] > winloss_data[team_b]) else 0

            matchups.append(feature_diff)

    with open("matchups.csv", mode='w', newline='') as writefile_matchups:
        writer = csv.DictWriter(writefile_matchups, fieldnames=matchups[0].keys())  # Define column headers
        writer.writeheader()  # Write header row
        writer.writerows(matchups)  # Write data rows
        
            
if __name__ == '__main__':
    #team_ids()
    #team_stats()
    #create_WL_ratios()
    #create_matchup_csv()
    pass

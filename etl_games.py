import os
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import numpy as np
import json

load_dotenv()
API_KEY = os.getenv('CFBD_API_KEY')
BASE_URL = "https://api.collegefootballdata.com" 
headers = {'Authorization': f'Bearer {API_KEY}'}
engine = create_engine(os.getenv('DATABASE_URL'))

def pull_games(season):
    response = requests.get(BASE_URL + '/games', headers=headers, params={'year':season, 'seasonType':'regular'})
    games = pd.DataFrame(response.json())
    games.to_csv(f'data/raw_games_{season}.csv', index=False)
    return games

def get_team_id(engine):
    teams = pd.read_sql('SELECT team_id FROM teams', engine)
    return set(teams['team_id'])

def clean_games(raw, team_ids):
    is_fbs = (raw['homeClassification'] == 'fbs') | (raw['awayClassification'] == 'fbs')
    df = raw[is_fbs].copy()
    assert(df['homeId'].isin(team_ids).all())
    assert(df['awayId'].isin(team_ids).all())
    df['game_date'] = pd.to_datetime(df['startDate']).dt.tz_convert('America/Chicago').dt.date
    raw_date = pd.to_datetime(df['startDate'].str[:10]).dt.date
    df['game_date'] = np.where(df['startTimeTBD'], raw_date, df['game_date'])
    df = df.rename(columns={
        'id':'game_id',
        'homeId':'home_team_id',
        'awayId':'away_team_id',
        'homePoints':'home_points',
        'awayPoints':'away_points',
        'neutralSite':'neutral_site'
    })
    df = df[['game_id', 'season', 'week', 'game_date', 'home_team_id', 'away_team_id', 'home_points', 'away_points', 'neutral_site']]
    df['home_points'] = df['home_points'].astype('Int64')
    df['away_points'] = df['away_points'].astype('Int64')
    return df

def flatten_team_stats(data):
    rows = []
    for game in data:
        for team in game['teams']:
            cats = {s['category']: s['stat'] for s in team['stats']}
            yards = cats.get('totalYards')
            turnovers = cats.get('turnovers')
            rush = cats.get('rushingAttempts')
            pass_att = cats.get('completionAttempts')
            if rush is not None:
                rush = int(rush)
            if yards is not None:
                yards = int(yards)
            if turnovers is not None:
                turnovers = int(turnovers)
            if pass_att is not None:
                pass_att = int(pass_att.split('-')[1])
            plays = None
            if pass_att is not None and rush is not None:
                plays = rush + pass_att
            rows.append({
                  'game_id': game['id'],
                  'team_id': team['teamId'],
                  'plays': plays,
                  'yards': yards,
                  'turnovers': turnovers
            })
    stats = pd.DataFrame(rows)
    return stats

def pull_team_stats(season, weeks):
    frames=[]
    for week in weeks:
        response = requests.get(BASE_URL + '/games/teams', headers=headers, params={'year':season, 'week':week, 'seasonType':'regular'})
        response.raise_for_status()
        week_stat = flatten_team_stats(response.json())
        with open(f'data/raw_gameteams_{season}_w{week}.json', 'w') as f:
            json.dump(response.json(), f)
        frames.append(week_stat)
    combined = pd.concat(frames, ignore_index=True)
    return combined

def load_team_stats(season, weeks):
    frames=[]
    for week in weeks:
        with open(f'data/raw_gameteams_{season}_w{week}.json') as f:
            data = json.load(f)
        frames.append(flatten_team_stats(data))
    combined_load = pd.concat(frames, ignore_index=True)
    return combined_load

team_stats = load_team_stats(2026, range(1, 7 + 1))
raw = pd.read_csv('data/raw_games_2026.csv')
team_ids = get_team_id(engine)
games = clean_games(raw, team_ids)
print(games.shape)
print(games.dtypes)
print(games.head())

print(team_stats.shape)
mask = team_stats['game_id'].isin(games['game_id'])
team_stats = team_stats[mask].copy()
print(team_stats.shape)
print(team_stats['team_id'].isin(team_ids).all())

print(team_stats.groupby('game_id').size().value_counts())

print(team_stats['game_id'].nunique())
print(team_stats.duplicated().sum())


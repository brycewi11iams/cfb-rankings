import os
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import numpy as np

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

raw = pd.read_csv('data/raw_games_2026.csv')
team_ids = get_team_id(engine)
games = clean_games(raw, team_ids)
print(games.shape)
print(games.dtypes)
print(games.head())



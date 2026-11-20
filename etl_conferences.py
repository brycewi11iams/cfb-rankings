import os
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text
import numpy as np
import json

load_dotenv()
API_KEY = os.getenv('CFBD_API_KEY')
BASE_URL = "https://api.collegefootballdata.com" 
headers = {'Authorization': f'Bearer {API_KEY}'}
engine = create_engine(os.getenv('DATABASE_URL'))

conference_sql = text("""
        INSERT INTO team_conferences (team_id, season, conference)
        VALUES (:team_id, :season, :conference)
        ON CONFLICT (team_id, season) DO UPDATE SET 
            conference = EXCLUDED.conference
    """)

def pull_conferences(season):
    response = requests.get(BASE_URL + '/teams/fbs', headers=headers, params={'year':season})
    response.raise_for_status()
    conferences = pd.DataFrame(response.json())
    conferences.to_csv(f'data/raw_conferences_{season}.csv', index=False)
    conferences['season'] = season
    conferences = conferences.rename(columns={
        'id':'team_id'
    })
    conferences = conferences[['team_id', 'season', 'conference']]
    return conferences

if __name__ == '__main__':
    df_2025 = pull_conferences(2025)
    df_2026 = pull_conferences(2026)
    print('2025 shape', df_2025.shape)
    print('2026 shape', df_2026.shape)
    print('2025 conference null', df_2025['conference'].isna().sum())
    print('2026 conference null', df_2026['conference'].isna().sum())
    print('2025 dups', df_2025['team_id'].duplicated().sum())
    print('2026 dups', df_2026['team_id'].duplicated().sum())
    ND = df_2026[df_2026['team_id'] == 87]
    ucon = df_2026[df_2026['team_id'] == 41]
    ND_25 = df_2025[df_2025['team_id'] == 87]
    ucon_25 = df_2025[df_2025['team_id'] == 41]
    print('ND', ND)
    print('uconn', ucon)
    print('2025 ND', ND_25)
    print('ucon_25', ucon_25)
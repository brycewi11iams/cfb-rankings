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

def load_conferences(seasons):
    with engine.begin() as conn:
        for season in seasons:
            df = pull_conferences(season)
            rows = df.to_dict('records')
            conn.execute(conference_sql, rows)
            print(season, len(rows))
        

if __name__ == '__main__':
   pass
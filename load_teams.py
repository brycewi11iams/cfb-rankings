import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text 
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('CFBD_API_KEY')
BASE_URL = "https://api.collegefootballdata.com"
headers = {'Authorization': f'Bearer {API_KEY}'}

response = requests.get(BASE_URL + '/teams', headers=headers, params={'year': 2026})
response.raise_for_status()
print('status', response.status_code)

teams = pd.DataFrame(response.json())

teams = teams[['id', 'school', 'classification']]

teams = teams[teams['classification'].isin(['fbs', 'fcs'])]
teams = teams.rename(columns={
    'id':'team_id',
    'school':'team_name'
})

teams['classification'] = teams['classification'].str.upper()

print(len(teams))
print(teams['classification'].value_counts())

# where is my database?
DATABASE_URL = os.getenv('DATABASE_URL')            # COPY the name from test_setup.py
engine = create_engine(DATABASE_URL)

# the SQL, written once, with named placeholders
upsert_sql = text("""
    INSERT INTO teams (team_id, team_name, classification)
    VALUES (:team_id, :team_name, :classification)
    ON CONFLICT (team_id) DO UPDATE
    SET team_name = EXCLUDED.team_name,
        classification = EXCLUDED.classification
""")

# the data, as a list of dictionaries, one per row
rows = teams.to_dict("records")

# run it
with engine.begin() as conn:
    conn.execute(upsert_sql, rows)          # what goes here?
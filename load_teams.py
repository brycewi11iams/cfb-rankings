import os
import requests
import pandas as pd
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
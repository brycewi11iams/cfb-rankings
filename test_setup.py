import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Read the settings from the .env file
load_dotenv()
api_key = os.getenv("CFBD_API_KEY")
db_url = os.getenv("DATABASE_URL")

# Part 1: call the CFBD API
url = "https://api.collegefootballdata.com/teams/fbs?year=2026"
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(url, headers=headers)
print("API status code:", response.status_code)

if response.status_code == 200:
    teams = response.json()
    print("FBS team count:", len(teams))
else:
    print("API call failed:", response.text)

# Part 2: connect to Postgres
engine = create_engine(db_url)
with engine.connect() as conn:
    version = conn.execute(text("SELECT version()")).scalar()
print("Postgres version:", version)
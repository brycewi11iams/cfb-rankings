import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CFBD_API_KEY")        # COPY the variable name from test_setup.py
BASE_URL = "https://api.collegefootballdata.com"                  # COPY the base URL from test_setup.py
headers = {"Authorization": f"Bearer {API_KEY}"}   # COPY if test_setup.py does it differently

# 1. call the endpoint
response = requests.get(BASE_URL + "/teams", headers=headers, params={"year": 2026})
print("status:", response.status_code)

# 2. JSON into a DataFrame
teams = pd.DataFrame(response.json())

# 3. every field CFBD gives you
print(teams.columns.tolist())

# 4. classification counts, including empty values
print(teams["classification"].value_counts(dropna=False))

# 5. a few FCS rows
print(teams[teams["classification"] == "fcs"].head())
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text

name_fixes = {
    'Pitt': 'Pittsburgh',
    'NDSU': 'North Dakota State',
    'Umass': 'Massachusetts',
    'JMU': 'James Madison',
    'USF': 'South Florida',
    'UNT': 'North Texas',
    'Louisana Tech': 'Louisiana Tech',
    'PITT': 'Pittsburgh',
    'TENNESSEE': 'Tennessee',
    'MISSOURI': 'Missouri'
}
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def clean_rankings(path, season, week):
    df = pd.read_excel(path, sheet_name = 'Rankings', header=1)
    df = df[['Team', 'Rank']]
    df = df.dropna(subset=['Rank'])
    df['Rank'] = df['Rank'].astype(int)
    df = df.rename(columns = {'Team': 'team_name', 'Rank': 'rank_num'})
    df['season'] = season
    df['week'] = week
    return df

def add_team_id(df):
    df = df.copy()
    df['team_name'] = df['team_name'].replace(name_fixes)
    team_sql = text(""" SELECT team_id, team_name FROM teams """)
    team = pd.read_sql(team_sql, engine)
    id_lookup = team.set_index('team_name')['team_id']
    df['team_id'] = df['team_name'].map(id_lookup)
    return df

def store_rows_excel(df):
    season = int(df['season'].loc[0])
    week = int(df['week'].iloc[0])
    sql = text("""
    INSERT INTO weekly_rankings (team_id, season, week, rank_num)
                VALUES (:team_id, :season, :week, :rank_num)
    """)
    sql_delete = text("""
    DELETE FROM weekly_rankings WHERE season = :season AND week = :week
    """)
    records = df.astype(object).where(df.notna(), None).to_dict('records')
    delete = {'season': season, 'week': week}
    with engine.begin() as conn:
        conn.execute(sql_delete, delete)
        conn.execute(sql, records)


if __name__ == '__main__':
    # for i in range(5, 14):
    #     df = clean_rankings(f'C:/Users/baw61/Projects/cfb-rankings/data/College_Football_Rankings_2026_week_{i}.xlsx', 2026, i-1)
    #     print(i)
    #     team = add_team_id(df)
    #     mask = team['team_id'].isna()
    #     na_teams = team[mask]
    #     print(na_teams['team_name'])
    #     store_rows_excel(team)
    df = clean_rankings('C:/Users/baw61/Projects/cfb-rankings/data/College Football Rankings 2025_final_copy.xlsx', 2025, 16)
    team = add_team_id(df)
    mask = team['team_id'].isna()
    na_teams = team[mask]
    print(na_teams['team_name'])
    store_rows_excel(team)

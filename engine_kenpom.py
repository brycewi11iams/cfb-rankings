import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text

FCS_WEIGHT = 0.5
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def load_games(season, as_of_week):
    sql = text("""
    SELECT team_id, opp_id, week, site, off_pts_per_drive, def_pts_per_drive, game_id
    FROM team_game_stats
     WHERE season = :season AND week <= :week
    """)
    df = pd.read_sql(sql, engine, params={'season': season, 'week': as_of_week})

    fcs_sql = text("""
    SELECT team_id
    FROM teams
    WHERE classification = 'FCS'
    """)
    df2 = pd.read_sql(fcs_sql, engine)
    fcs_ids = set(df2['team_id'])

    fcs_team = df['team_id'].isin(fcs_ids)
    fcs_other_team = df['opp_id'].isin(fcs_ids)

    df['team_key'] = np.where(fcs_team, -1, df['team_id'])
    df['opp_key'] = np.where(fcs_other_team, -1, df['opp_id'])

    fcs_check = (df['team_key'] == -1) | (df['opp_key'] == -1)
    df['weight'] = np.where(fcs_check, FCS_WEIGHT, 1)
    return df

if __name__ == '__main__':
    test = load_games(2026, 9)
    print(test.shape)
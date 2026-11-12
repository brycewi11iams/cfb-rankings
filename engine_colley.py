import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def load_colley_games(season, as_of_week):
    games_sql = text("""
    SELECT game_id, team_id, opp_id, week, result
    FROM team_games
    WHERE season = :season AND week <= :week
    """)

    df = pd.read_sql(games_sql, engine, params={'season': season, 'week': as_of_week})

    fcs_sql = text("""
    SELECT team_id
    FROM teams
    WHERE classification = 'FCS'
    """)
    fcs_df = pd.read_sql(fcs_sql, engine)
    fcs_ids = set(fcs_df['team_id'])

    fcs_team = df['team_id'].isin(fcs_ids)
    fcs_other_team = df['opp_id'].isin(fcs_ids)

    df['team_key'] = np.where(fcs_team, -1, df['team_id'])
    df['opp_key'] = np.where(fcs_other_team, -1, df['opp_id'])
    print('shape', df.shape)
    fcs_count = df['team_key'] == -1
    fcs_count_opp = df['opp_key'] == -1
    print('fcs_team',fcs_count.sum())
    print('fcs_opp', fcs_count_opp.sum())
    wins = df['result'] == 'W'
    losses = df['result'] == 'L'
    print('wins', wins.sum())
    print('losses', losses.sum())
    group = df.groupby('game_id').size()
    print('game_id', (group != 2).sum())
    return df

if __name__ == '__main__':
    load_colley_games(2026, 10)
    load_colley_games(2026, 9)
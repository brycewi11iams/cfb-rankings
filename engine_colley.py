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
    return df

def build_colley(season, as_of_week):
    df = load_colley_games(season, as_of_week)
    pairs = pd.crosstab(df['team_key'], df['opp_key'])
    games_per_team = pairs.sum(axis=1)
    mask_losses = df['result'] == 'L'
    losses = mask_losses.groupby(df['team_key']).sum()
    losses = losses.reindex(games_per_team.index)
    mask_wins = df['result'] == 'W'
    wins = mask_wins.groupby(df['team_key']).sum()
    wins = wins.reindex(games_per_team.index)

    pairs_array = pairs.to_numpy()
    c = np.diag(games_per_team + 2) - pairs_array
    b = 1 + 1/2 * (wins - losses)
    b = b.to_numpy()
    keys = games_per_team.index
    return c,b,keys

if __name__ == '__main__':
    c, b, keys = build_colley(2026, 10)
    
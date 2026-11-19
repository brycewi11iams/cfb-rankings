import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text
from engine_kenpom import store_rows, get_weeks

FCS_WEIGHT = 0.5
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def load_massey_games(season, as_of_week):
    games_sql = text("""
    SELECT game_id, team_id, opp_id, week, result, margin
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


def build_massey(season, as_of_week):
    df = load_massey_games(season, as_of_week)
    pairs = pd.crosstab(df['team_key'], df['opp_key'])
    games_per_team = pairs.sum(axis=1)

    pairs_array = pairs.to_numpy()
    m = np.diag(games_per_team) - pairs_array
    p = df.groupby('team_key')['margin'].sum()
    p = p.reindex(games_per_team.index)
    p = p.to_numpy()  
    keys = games_per_team.index
    m_copy = m.copy()
    p_copy = p.copy()
    m_copy[-1, :] = 1
    p_copy[-1] = 0

    return m_copy, p_copy, keys

def run_massey(season, as_of_week):
    m, p, keys = build_massey(season, as_of_week)
    ratings = np.linalg.solve(m, p)
    ratings = pd.DataFrame(ratings, index=keys, columns=['rating'])
    names_sql = text("""
    SELECT team_id, team_name FROM teams
    """)
    names = pd.read_sql(names_sql, engine)
    names_lookup = names.set_index('team_id')['team_name']
    ratings['team_name'] = ratings.index.map(names_lookup)
    ratings['team_name'] = ratings['team_name'].fillna('FCS (pooled)')
    ratings = ratings.sort_values(by='rating', ascending=False)
    return ratings

def prepare_massey_rows(ratings, season, week):
    non_fcs = ratings.index != -1
    ratings = ratings[non_fcs].copy()
    ratings['off_rating'] = None
    ratings['def_rating'] = None
    ratings['score'] = ratings['rating']
    ratings['rank_num'] = ratings['score'].rank(method='first', ascending=False).astype(int)
    ratings['team_id'] = ratings.index
    ratings['season'] = season
    ratings['week'] = week
    ratings['engine'] = 'massey'
    ratings = ratings[['team_id', 'season', 'week', 'engine', 'score', 'rank_num', 'off_rating', 'def_rating']]
    ratings = ratings.reset_index(drop=True)
    return ratings

if __name__ == '__main__':
    ratings = run_massey(2026, 11)
    rows = prepare_massey_rows(ratings, 2026, 11)
    print(rows.shape)
    print(rows['rank_num'].nunique())
    mask = rows['rank_num'] ==1
    print(rows[mask])
    fcs = rows['team_id'] == -1
    print(fcs.sum())
    print(rows['engine'].nunique())
    

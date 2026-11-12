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

def run_colley(season, as_of_week):
    c, b, keys = build_colley(season, as_of_week)
    ratings = np.linalg.solve(c, b)
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

def prepare_colley_rows(ratings, season, week):
    non_fcs = ratings.index != -1
    ratings = ratings[non_fcs].copy()
    ratings['off_rating'] = None
    ratings['def_rating'] = None
    ratings['score'] = ratings['rating']
    ratings['rank_num'] = ratings['score'].rank(method='first', ascending=False).astype(int)
    ratings['team_id'] = ratings.index
    ratings['season'] = season
    ratings['week'] = week
    ratings['engine'] = 'colley'
    ratings = ratings[['team_id', 'season', 'week', 'engine', 'score', 'rank_num', 'off_rating', 'def_rating']]
    ratings = ratings.reset_index(drop=True)
    return ratings


if __name__ == '__main__':
    ratings = run_colley(2026, 10)
    rows = prepare_colley_rows(ratings, 2026, 10)
    print(rows.shape)
    print(rows['rank_num'].nunique())
    print(rows['rank_num'].max())
    print(rows['rank_num'].min())
    num_1 = rows['rank_num'] == 1
    print(rows[num_1])
    fcs_check = rows['team_id'] == -1
    print(fcs_check.sum())
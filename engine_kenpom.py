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
    site = {'A': -1, 'N': 0, 'H': 1}
    df['site_num'] = df['site'].map(site)
    return df


def fit_ratings(df):
    league_avg = (df['off_pts_per_drive'] * df['weight']).sum() / df['weight'].sum()
    off_distinct_key = df['team_key'].unique()
    def_distinct_key = df['opp_key'].unique()
    off_rating = pd.Series(0.0, index=off_distinct_key)
    def_rating = pd.Series(0.0, index=def_distinct_key)
    hfa = 0.0

    for i in range(100):
        df['off_resid'] = df['off_pts_per_drive'] - league_avg - df['opp_key'].map(def_rating) - hfa * df['site_num']
        new_off = (df['off_resid'] * df['weight']).groupby(df['team_key']).sum() / df['weight'].groupby(df['team_key']).sum()
        new_off = new_off - new_off.mean()
        df['def_resid'] = df['def_pts_per_drive'] - league_avg - df['opp_key'].map(new_off) - hfa * (-df['site_num'])
        new_def = (df['def_resid'] * df['weight']).groupby(df['team_key']).sum() / df['weight'].groupby(df['team_key']).sum()
        new_def = new_def - new_def.mean()
        leftover = df['off_pts_per_drive'] - league_avg - df['team_key'].map(new_off) - df['opp_key'].map(new_def)
        top = (df['weight'] * df['site_num'] * leftover).sum()
        bottom = (df['weight'] * df['site_num'] * df['site_num']).sum()
        new_hfa = top / bottom
        hfa_change = abs(new_hfa - hfa)

        off_change = (new_off - off_rating).abs().max()
        def_change = (new_def - def_rating).abs().max()
        off_rating = new_off
        def_rating = new_def
        hfa = new_hfa
        change = max(off_change, def_change, hfa_change)
        if change < .0001:
            break
    return off_rating, def_rating, hfa, league_avg

def run_engine(season, as_of_week):
    df = load_games(season, as_of_week)
    off, defn, hfa, league_avg = fit_ratings(df)
    ratings = pd.DataFrame({'off': off, 'def': defn})
    ratings['net'] = off - defn
    names_sql = text("""
    SELECT team_id, team_name
    FROM teams
    """)
    names = pd.read_sql(names_sql, engine)
    names_lookup = names.set_index('team_id')['team_name']
    ratings['team_name'] = ratings.index.map(names_lookup)
    ratings['team_name'] = ratings['team_name'].fillna('FCS (pooled)')
    return ratings, hfa, league_avg

def prepare_rows(ratings, league_avg, season, week):
    non_fcs = ratings.index != -1
    ratings = ratings[non_fcs].copy()
    ratings['off'] = ratings['off'] - ratings['off'].mean()
    ratings['def'] = ratings['def'] - ratings['def'].mean()
    ratings['net'] = ratings['off'] - ratings['def']
    ratings['off_rating'] = (league_avg + ratings['off']) * 12
    ratings['def_rating'] = (league_avg + ratings['def']) * 12
    ratings['score'] = ratings['off_rating'] - ratings['def_rating']
    ratings['rank_num'] = ratings['score'].rank(method='first', ascending=False).astype(int)
    ratings['team_id'] = ratings.index
    ratings['season'] = season
    ratings['week'] = week
    ratings['engine'] = 'kenpom'
    ratings = ratings[['team_id', 'season', 'week', 'engine', 'score', 'rank_num', 'off_rating', 'def_rating']]
    ratings = ratings.reset_index(drop=True)
    print(ratings['score'].mean())
    return ratings

if __name__ == '__main__':
    ratings, hfa, league_avg = run_engine(2025, 16)
    ratings = ratings[ratings.index != -1]
    ratings = ratings.sort_values(by='net', ascending=False)
    rows = prepare_rows(ratings, league_avg, 2025, 16)
    print(rows['rank_num'].max())
    print(rows['rank_num'].nunique())
    print(rows.head(5).sort_values(by='rank_num'))

import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text
from engine_kenpom import store_rows, get_weeks

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
G6_SCALE = 0.7

def load_resume_inputs(season, as_of_week):
    sql = text("""
    SELECT te.team_id, te.p4_games, te.g6_games, te.p4_win_pct, te.g6_win_pct, too.p4_opp_wp, 
            too.g6_opp_wp, top.p4_oopp_wp, top.g6_oopp_wp
    FROM team_asof_record te
    JOIN team_asof_opp_avg too ON te.team_id = too.team_id AND te.season = too.season AND te.as_of_week = too.as_of_week
    JOIN team_asof_oopp_avg top ON too.team_id = top.team_id AND too.season = top.season AND too.as_of_week = top.as_of_week
    WHERE te.season = :season AND te.as_of_week = :as_of_week
    """)

    df = pd.read_sql(sql, engine, params={'season': season, 'as_of_week': as_of_week})
    return df

def score_resume(df, g6_scale=G6_SCALE):
    df['p4_opp_wp'] = df['p4_opp_wp'].fillna(.5)
    df['g6_opp_wp'] = df['g6_opp_wp'].fillna(.5)
    df['p4_oopp_wp'] = df['p4_oopp_wp'].fillna(.5)
    df['g6_oopp_wp'] = df['g6_oopp_wp'].fillna(.5)
    df['p4_score'] = ((3 * df['p4_win_pct']) + (2 * df['p4_opp_wp']) + (df['p4_oopp_wp'])) / 6
    df['g6_score'] = ((3 * df['g6_win_pct']) + (2 * df['g6_opp_wp']) + (df['g6_oopp_wp'])) / 6
    df['p4_score'] = df['p4_score'].fillna(0)
    df['g6_score'] = df['g6_score'].fillna(0)
    total = df['g6_games'] + df['p4_games']
    total = total.where(total > 0)
    df['score'] = ((df['g6_games'] * df['g6_score'] * g6_scale) + (df['p4_games'] * df['p4_score'])) / total
    df['score'] = df['score'].astype(float)
    return df

def run_resume(season, as_of_week):
    df = load_resume_inputs(season, as_of_week)
    score = score_resume(df)
    mask = (df['p4_games'] + df['g6_games'] > 0).copy()
    score = score[mask].copy()
    names_sql = text("""
    SELECT team_id, team_name FROM teams
    """)
    names = pd.read_sql(names_sql, engine)
    names_lookup = names.set_index('team_id')['team_name']
    score['team_name'] = score['team_id'].map(names_lookup)
    score = score.sort_values(by='score', ascending=False)
    return score

def prepare_resume_rows(score, season, week):
    score = score.copy()
    score['off_rating'] = None
    score['def_rating'] = None
    score['rank_num'] = score['score'].rank(method='first', ascending=False).astype(int)
    score['season'] = season
    score['week'] = week
    score['engine'] = 'resume'
    score = score[['team_id', 'season', 'week', 'engine', 'score', 'rank_num', 'off_rating', 'def_rating']]
    score = score.reset_index(drop=True)
    return score

def run_and_store_resume(season, week):
    score = run_resume(season, week)
    rows = prepare_resume_rows(score, season, week)
    store_rows(rows)
    print(season, week, len(rows))

def backfill_resume():
    for season in [2025, 2026]:
        weeks = get_weeks(season)
        for week in weeks:
            run_and_store_resume(season, week)
    
if __name__ == '__main__':
    ratings = run_resume(2026, 12)
    rows = prepare_resume_rows(ratings, 2026, 12)
    print('rows shape', rows.shape)
    print('rank unique', rows['rank_num'].nunique())
    print('rank min', rows['rank_num'].min())
    print('rank max', rows['rank_num'].max())
    print('first team_ids', rows['team_id'].head(3).tolist())
    print(ratings[['team_name', 'score']].head(10))




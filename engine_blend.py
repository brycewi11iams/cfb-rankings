import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text
from engine_kenpom import store_rows, get_weeks

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def combined_engines(season, week):
    sql = text("""
    SELECT 
        team_id,
        MAX(er.score) FILTER (WHERE er.engine = 'kenpom') AS kenpom,
        MAX(er.score) FILTER (WHERE er.engine = 'colley') AS colley,
        MAX(er.score) FILTER (WHERE er.engine = 'massey') AS massey,
        MAX(er.score) FILTER (WHERE er.engine = 'resume') AS resume
    FROM engine_results er
    WHERE season = :season AND week = :week
    GROUP BY team_id
    """)
    df = pd.read_sql(sql, engine, params={'season': season, 'week': week})
    return df

def standardize_scores(df):
    df = df.copy()
    df['combined_score'] = 0
    scores = df[['kenpom', 'colley', 'massey', 'resume']]
    for score in scores:
        avg = df[score].mean()
        sd = df[score].std()
        new_score = (df[score] - avg) / sd
        df['combined_score'] += new_score
        df[f'{score}_score'] = new_score
    df['combined_score'] = df['combined_score'] / 4
    return df

def prepare_blend_rows(season, week):
    df = combined_engines(season, week)
    scores = standardize_scores(df)
    scores = scores.copy()
    scores['score'] = scores['combined_score']
    scores['off_rating'] = None
    scores['def_rating'] = None
    scores['rank_num'] = scores['score'].rank(method='first', ascending=False).astype(int)
    scores['season'] = season
    scores['week'] = week
    scores['engine'] = 'blend'
    scores = scores[['team_id', 'season', 'week', 'engine', 'score', 'rank_num', 'off_rating', 'def_rating']]
    scores = scores.reset_index(drop=True)
    return scores

def run_and_store_blend(season, week):
    rows = prepare_blend_rows(season, week) 
    store_rows(rows)
    print(season, week, len(rows))

# def backfill_resume():
#     for season in [2025, 2026]:
#         weeks = get_weeks(season)
#         for week in weeks:
#             run_and_store_blend(season, week)

if __name__ == '__main__':
    # df = combined_engines(2026, 12)
    # df_25 = combined_engines(2025, 15)
    # print(df.shape)
    # print(df.isna().sum())
    # ND = df[df['team_id'] == 87]
    # print(ND.to_string())
    # print(df_25.shape)
    # df = combined_engines(2026, 12)
    # scores = standardize_scores(df)
    # print(scores.shape)
    # print(scores['combined_score'].mean())
    # print(scores['combined_score'].std())
    # print(scores['kenpom_score'].mean())
    # print(scores['kenpom_score'].std())
    # print(scores['colley_score'].mean())
    # print(scores['colley_score'].std())
    # print(scores['massey_score'].mean())
    # print(scores['massey_score'].std())
    # print(scores['resume_score'].mean())
    # print(scores['resume_score'].std())
    # scores = scores.sort_values(by='combined_score', ascending=False)
    # print(scores.head(10))
    # df = prepare_blend_rows(2026, 12)
    # print(df.shape)
    # print(df['rank_num'].nunique())
    # num_1 = df[df['rank_num'] == 1]
    # print(num_1['team_id'])
    run_and_store_blend(2026, 12)
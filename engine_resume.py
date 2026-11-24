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
    df['score'] = ((df['g6_games'] * df['g6_score'] * g6_scale) + (df['p4_games'] * df['p4_score'])) / (df['g6_games'] + df['p4_games'])
    return df


if __name__ == '__main__':
    df = load_resume_inputs(2026, 12)
    # print(df.shape)
    # print(df['team_id'].nunique())
    # print(df.isna().sum())
    # df_2025 = load_resume_inputs(2025, 16)
    # print(df_2025.shape)
    score = score_resume(df)
    print(score['score'].isna().sum())
    print(score['score'].min())
    print(score['score'].max())
    ND = score[score['team_id'] == 87]
    print(ND)



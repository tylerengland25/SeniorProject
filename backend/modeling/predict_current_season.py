import pandas as pd
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from backend.scraping.Game_Stats import convert_poss


def convert_odds(odds):
    if odds < 0:
        odds = odds * -1
        return odds / (100 + odds)
    else:
        return 100 / (100 + odds)


def calc_profit(stake, odds):
    if odds < 0:
        odds = odds * -1
        return stake / (odds / 100)
    else:
        return stake * (odds / 100)


def load_data_classifier():
    """
    Loads data and splits into X and Y training and testing sets
    :return:
    """
    x_df = pd.read_csv("backend/data/current_last_five_games.csv")
    x_df.fillna(0, inplace=True)
    y_df = pd.read_csv("backend/data/current_season_stats.csv")
    odds = pd.read_csv("backend/data/odds/odds.csv")

    df = pd.merge(y_df, x_df,
                  how="left",
                  left_on=["Home", "Week", "Year"],
                  right_on=["team", "week", "year"])

    df = pd.merge(df, x_df,
                  how="left",
                  left_on=["Away", "Week", "Year"],
                  right_on=["team", "week", "year"])

    df = df[(df["Week"] > 5) | (df["Year"] != 2010)]
    df.set_index(["Home", "Away", "Week", "Year"], inplace=True)

    x_cols = []
    for col in df.columns:
        if "poss" in col:
            df[col] = df[col].apply(lambda x: convert_poss(x) if ":" in x else x)
            x_cols.append(col)
        elif col[-4:] in ["_1_x", "_1_y"] \
                and "named" not in col and "opponent" not in col and "season_length" not in col:
            x_cols.append(col)
            df[col] = df[col] * 3
        elif col[-4:] in ["_2_x", "_2_y"] \
                and "named" not in col and "opponent" not in col and "season_length" not in col:
            x_cols.append(col)
            df[col] = df[col] * 3
        elif col[-4:] in ["_3_x", "_3_y"] \
                and "named" not in col and "opponent" not in col and "season_length" not in col:
            x_cols.append(col)
            df[col] = df[col] * 2

        elif col[-4:] in ["_4_x", "_4_y"] \
                and "named" not in col and "opponent" not in col and "season_length" not in col:
            x_cols.append(col)
            df[col] = df[col] * 2
        elif col[-4:] in ["_5_x", "_5_y"] \
                and "named" not in col and "opponent" not in col and "season_length" not in col:
            x_cols.append(col)
            df[col] = df[col] * 2

    # Standardized X values
    # x_cols = ["3rd_att", "3rd_cmp", "3rd_att_def", "3rd_cmp_def", "4th_att", "4th_cmp", "4th_att_def", "4th_cmp_def",
    #           "cmp", "cmp_def", "poss", "total_y", "total_y_def"]
    x_cols = ["cmp_pct", "cmp_pct_def", "3rd_pct", "3rd_pct_def", "4th_pct", "4th_pct_def", "fg_pct", "yds_per_rush",
              "yds_per_rush_def", "yds_per_att", "yds_per_att_def", "yds_per_ply", "yds_per_ply_def", "poss",
              "pass_yds", "pass_yds_def", "pen_yds", "pen_yds_def", "punts", "punts_def", "rush_yds", "rush_yds_def",
              "sacks", "sacks_def", "score", "score_def", "cmp", "cmp_def", "total_y", "total_y_def", "pts_per_ply",
              "pts_per_ply_def", "punts_per_ply", "punts_per_ply_def", "pts_per_yd", "pts_per_yd_def"]

    final_cols = []
    for col in x_cols:
        for i in range(1, 6):
            final_cols.append(col + "_" + str(i) + "_x")
            final_cols.append(col + "_" + str(i) + "_y")
    X = df[final_cols]
    X.astype(float)
    scaler = StandardScaler()
    X_standardized = pd.DataFrame(scaler.fit_transform(X))
    X_standardized.index = X.index

    # Y values
    df = pd.merge(df, odds.iloc[:, 1:],
                  how="left",
                  left_on=["Home", "Away", "Week", "Year"],
                  right_on=["Home", "Away", "Week", "Year"])
    df.set_index(["Home", "Away", "Week", "Year"], inplace=True)
    df["win_lose"] = df["H_Score"] - df["A_Score"]
    df["win_lose"] = df["win_lose"] > 0
    df["win_lose"] = df["win_lose"].astype(int)
    y = df[["win_lose", "ML_h", "ML_a"]]
    y.index = df.index

    return X_standardized, y


def main():
    # Load data and model
    odds = pd.read_csv("backend/data/odds/2021/Week_11.csv")
    current_week = 11
    X, y = load_data_classifier()
    svm = pickle.load(open("backend/modeling/models/svm.pkl", "rb"))
    X = X.reset_index()
    y = y.reset_index()
    X = X[(X["Year"] == 2021) & (X["Week"] == current_week)]

    # Predict
    svm_prob = svm.predict_proba(X.drop(["Home", "Away", "Week", "Year"], axis=1))
    svm_odds = pd.DataFrame(svm_prob, columns=["away_win_prob", "home_win_prob"])
    odds = pd.merge(odds, svm_odds, how="left", left_index=True, right_index=True)
    odds["Home_odds_actual"] = odds["ML_h"].apply(lambda x: convert_odds(x))
    odds["Away_odds_actual"] = odds["ML_a"].apply(lambda x: convert_odds(x))
    odds["home_divergence"] = odds["home_win_prob"] - odds["Home_odds_actual"]
    odds["away_divergence"] = odds["away_win_prob"] - odds["Away_odds_actual"]
    betting_model = pickle.load(open("backend/modeling/models/betting_model.pkl", "rb"))
    odds["outcome_predict"] = betting_model.predict(odds[["away_win_prob", "home_win_prob", "ML_h", "ML_a",
                                                          "Home_odds_actual", "Away_odds_actual", "home_divergence",
                                                          "away_divergence"]])
    odds["potential_payout"] = np.where(odds["outcome_predict"],
                                        odds["ML_h"].apply(lambda x: calc_profit(100, x)),
                                        odds["ML_a"].apply(lambda x: calc_profit(100, x)))
    odds["bet"] = np.where(odds["outcome_predict"], odds["Home"], odds["Away"])
    odds["home_win_prob"] = odds["home_win_prob"].apply(lambda x: str(round(x * 100)) + "%")
    odds["away_win_prob"] = odds["away_win_prob"].apply(lambda x: str(round(x * 100)) + "%")
    odds["potential_payout"] = odds["potential_payout"].apply(lambda x: "$" + str(round(x)))
    odds = odds[["Home", "home_win_prob", "Away", "away_win_prob", "bet", "potential_payout"]]
    odds.to_csv("backend/data/predictions/Week_"+ str(current_week) + "_predictions.csv")


if __name__ == '__main__':
    main()

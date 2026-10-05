import pandas as pd

df = pd.read_csv("data/understat_player_stats_2025-26.csv")
print(df.columns.tolist())  

# Step 1: how many "full 90-minute games" each player's minutes add up to.
df["nineties"] = df["minutes"] / 90

# Step 2: convert raw season totals into per-90 rates.
# A player with 10 goals in 2000 minutes and a player with 10 goals in
# 1000 minutes should not look identical so per-90 fixes that.
per90_cols = {
    "goals": "goals_p90",
    "xg": "xg_p90",
    "np_xg": "np_xg_p90",
    "assists": "assists_p90",
    "xa": "xa_p90",
    "shots": "shots_p90",
    "key_passes": "key_passes_p90",
    "xg_chain": "xg_chain_p90",
    "xg_buildup": "xg_buildup_p90",
}

for raw_col, new_col in per90_cols.items():
    df[new_col] = df[raw_col] / df["nineties"]

# Step 3: group the per-90 metrics into functional pillars, matching
# the original project concept (Finishing, Creation, Buildup)
finishing_pillar = ["goals_p90", "xg_p90", "np_xg_p90", "shots_p90"]
creation_pillar = ["assists_p90", "xa_p90", "key_passes_p90"]
buildup_pillar = ["xg_chain_p90", "xg_buildup_p90"]

feature_cols = finishing_pillar + creation_pillar + buildup_pillar

# Keep player identity columns alongside the engineered features
final_df = df[["player", "team", "position", "nineties"] + feature_cols].copy()

print(final_df.shape)
print(final_df.head())
print(final_df.describe())

final_df.to_csv("data/player_features_p90.csv", index=False)
print("Saved to data/player_features_p90.csv")
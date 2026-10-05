import soccerdata as sd
import pandas as pd

# Pull the full 2025-26 Premier League season (completed, 38 matches)
understat = sd.Understat(leagues="ENG-Premier League", seasons="2025-26")
df = understat.read_player_season_stats()

print("Raw pull:", df.shape)

# Apply the 900-minute qualifier filter from the original project plan,
# to avoid small-sample noise (a sub with 2 assists in 150 minutes
# looking like a world-beater on a per-90 basis)
df_filtered = df[df["minutes"] >= 900].copy()

print("After 900-minute filter:", df_filtered.shape)
print(df_filtered.head())

# Save locally so we're not re-scraping every time we touch this data
df_filtered.to_csv("data/understat_player_stats_2025-26.csv", index=False)
print("Saved to data/understat_player_stats_2025-26.csv")
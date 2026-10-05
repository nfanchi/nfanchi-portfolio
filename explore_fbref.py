

import soccerdata as sd

understat = sd.Understat(leagues="ENG-Premier League", seasons="2024-25")
player_stats = understat.read_player_season_stats()
print(player_stats.shape)
print(player_stats.columns.tolist())

# Create the scraper for the Premier League, 2024-25 season
fbref = sd.FBref(leagues="ENG-Premier League", seasons="2024-25")

# Pull standard player season stats (goals, assists, minutes, etc.)
df = fbref.read_player_season_stats(stat_type="standard")

# Take a first look
print(df.shape)
print(df.head())
print(df.columns.tolist())
from statsbombpy import sb

# See every competition + season StatsBomb has made free to use
competitions = sb.competitions()

print(competitions.shape)
print(competitions[["competition_name", "season_name", "country_name"]].to_string())

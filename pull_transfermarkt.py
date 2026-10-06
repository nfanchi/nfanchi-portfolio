import duckdb

con = duckdb.connect()

# httpfs lets DuckDB read files directly over HTTPS, as if they were local
con.sql("INSTALL httpfs; LOAD httpfs;")

# player_valuations is a historical time series, one row per player per
# valuation date. We only want each player's most recent value, so we
# use a window function to rank each player's records by date and keep
# only the top-ranked (latest) one.
valuations = con.sql("""
    WITH ranked AS (
        SELECT
            player_id,
            market_value_in_eur,
            date,
            ROW_NUMBER() OVER (
                PARTITION BY player_id
                ORDER BY date DESC
            ) AS rn
        FROM read_csv_auto('https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/player_valuations.csv.gz')
    )
    SELECT player_id, market_value_in_eur, date AS valuation_date
    FROM ranked
    WHERE rn = 1
    AND date >= '2024-06-01'
""").df()

players = con.sql("""
    SELECT player_id, name AS player, date_of_birth
    FROM read_csv_auto('https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/players.csv.gz')
""").df()

# Join player names onto their latest valuation
merged = players.merge(valuations, on="player_id", how="inner")

print(merged.shape)
print(merged.head())

merged.to_csv("data/transfermarkt_valuations.csv", index=False)
print("Saved to data/transfermarkt_valuations.csv")
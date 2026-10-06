import pandas as pd
import difflib

features = pd.read_csv("data/player_features_p90.csv")
valuations = pd.read_csv("data/transfermarkt_valuations.csv")

# Names rarely match character-for-character between two independent
# sources (accents, punctuation, capitalization). Normalize both sides
# the same way before joining, so "Jo\u00e3o Pedro" and "Joao Pedro" count
# as the same player.
def normalize_name(name):
    name = str(name).lower().strip()
    name = (
        name.replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        .replace("ç", "c").replace("ü", "u")
    )
    return name

# Known one-off name mismatches that no automated matching approach can
# safely catch (genuinely different given names, not formatting issues).
# Found by spot-checking the unmatched list and documented here 
MANUAL_NAME_OVERRIDES = {
    "Mathis Cherki": "Rayan Cherki",  
    "Max Kilman": "Maximilian Kilman", 
    "Matìas Soulè Malvano": "Matías Soulè",
    "Kouadio Kone": "Manu Koné",
    "Julian Chabot": "Jeff Chabot",
    "Chimuanya Ugochukwu": "Lesley Ugochukwu",
    "Hannibal Mejbri": "Hannibal"
}
 
features["player"] = features["player"].replace(MANUAL_NAME_OVERRIDES)

features["name_key"] = features["player"].apply(normalize_name)
valuations["name_key"] = valuations["player"].apply(normalize_name)

merged = features.merge(
    valuations[["name_key", "market_value_in_eur", "valuation_date"]],
    on="name_key",
    how="left",
)

matched = merged["market_value_in_eur"].notna().sum()
total = len(merged)
print(f"Matched {matched} of {total} players ({matched/total:.0%})")

# Second pass: for anyone still unmatched, try fuzzy-matching their name
# against the valuations list (catches nicknames, alternate spellings,
# e.g. "Matthew Cash" vs "Matty Cash")
valuation_names = valuations["player"].tolist()
still_unmatched = merged[merged["market_value_in_eur"].isna()].index
 
fuzzy_fixed = 0
for idx in still_unmatched:
    original_name = merged.loc[idx, "player"]
    close = difflib.get_close_matches(original_name, valuation_names, n=1, cutoff=0.75)
    if close:
        match_row = valuations[valuations["player"] == close[0]].iloc[0]
        merged.loc[idx, "market_value_in_eur"] = match_row["market_value_in_eur"]
        merged.loc[idx, "valuation_date"] = match_row["valuation_date"]
        fuzzy_fixed += 1
 
print(f"Fuzzy pass recovered {fuzzy_fixed} more matches")

# Third pass: substring containment, using the already-normalized,
# accent-stripped name_key column. Catches cases where one side uses a
# fuller/legal name and the other a shorter common version
# (e.g. "kylian mbappe-lottin" vs "kylian mbappe") 
still_unmatched = merged[merged["market_value_in_eur"].isna()].index
valuation_keys = valuations[["name_key", "market_value_in_eur", "valuation_date"]]
 
substring_fixed = 0
for idx in still_unmatched:
    key = merged.loc[idx, "name_key"]
    candidates = valuation_keys[
        valuation_keys["name_key"].apply(lambda v: key in v or v in key)
    ]
    if len(candidates) == 1:
        merged.loc[idx, "market_value_in_eur"] = candidates.iloc[0]["market_value_in_eur"]
        merged.loc[idx, "valuation_date"] = candidates.iloc[0]["valuation_date"]
        substring_fixed += 1
 
print(f"Substring pass recovered {substring_fixed} more matches")

# Fourth pass: compare word sets rather than raw strings, ignoring order.
# Catches naming-convention differences, e.g. Korean family-name-first
# ("Lee Kang-In") vs given-name-first ("Kang-in Lee").
still_unmatched = merged[merged["market_value_in_eur"].isna()].index
valuation_keys["token_set"] = valuation_keys["name_key"].apply(lambda k: frozenset(k.split()))
 
tokenset_fixed = 0
for idx in still_unmatched:
    key_tokens = frozenset(merged.loc[idx, "name_key"].split())
    candidates = valuation_keys[valuation_keys["token_set"] == key_tokens]
    if len(candidates) == 1:
        merged.loc[idx, "market_value_in_eur"] = candidates.iloc[0]["market_value_in_eur"]
        merged.loc[idx, "valuation_date"] = candidates.iloc[0]["valuation_date"]
        tokenset_fixed += 1
 
print(f"Token-set pass recovered {tokenset_fixed} more matches")

# Fifth pass: is the shorter name's set of words a subset of the longer
# name's words, regardless of position? Catches middle names/extra
# surnames anywhere in the string, not just at the very start/end
# (e.g. "jonathan christian david" containing "jonathan" + "david",
# with "christian" in between breaking a plain substring check).
still_unmatched = merged[merged["market_value_in_eur"].isna()].index
 
subset_fixed = 0
for idx in still_unmatched:
    key_tokens = set(merged.loc[idx, "name_key"].split())
    candidates = valuation_keys[
        valuation_keys["token_set"].apply(
            lambda v: len(v) >=2 and (key_tokens.issubset(v) or v.issubset(key_tokens))
        )
    ]
    if len(candidates) == 1:
        merged.loc[idx, "market_value_in_eur"] = candidates.iloc[0]["market_value_in_eur"]
        merged.loc[idx, "valuation_date"] = candidates.iloc[0]["valuation_date"]
        subset_fixed += 1
 
print(f"Subset pass recovered {subset_fixed} more matches")
 
matched = merged["market_value_in_eur"].notna().sum()
print(f"Total matched: {matched} of {total} players ({matched/total:.0%})")

# Show a sample of players who still don't get a valuation match, so we can
# spot-check whether it's a real gap or a name-formatting mismatch
unmatched = merged[merged["market_value_in_eur"].isna()][["player", "team"]]
print("\nSample of unmatched players:")
print(unmatched.head(21))

merged = merged.drop(columns=["name_key"])
merged.to_csv("data/player_features_with_value.csv", index=False)
print("\nSaved to data/player_features_with_value.csv")
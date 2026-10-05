import pandas as pd
import difflib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# Load the per-90 features built in feature_engineering 
df = pd.read_csv("data/player_features_p90.csv")

#Taking out S from the positions because "Substitute" doesn't give me 
#any real info in terms of actual matching players based on similarity
df["position"] = df["position"].str.replace(" S", "").str.replace("S", "")

feature_cols = [
    "goals_p90", "xg_p90", "np_xg_p90", "shots_p90",
    "assists_p90", "xa_p90", "key_passes_p90",
    "xg_chain_p90", "xg_buildup_p90",
]

X = df[feature_cols]

# Standardize so no single metric (e.g. shots_p90, which has bigger raw
# values) dominates the distance calculation just because of its scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Compute similarity between every player and every other player all at once
# This produces a 340x340 matrix where cell [i, j] is how similar
# player i is to player j (1.0 = identical profile, -1.0 = opposite).
similarity_matrix = cosine_similarity(X_scaled)
    
#actual function for finding similar players
def find_similar_players(player_name, top_n=5):
    """Given a player's name, return their top_n most statistically
    similar players based on per-90 attacking/creative output."""
 
    all_names = df["player"].tolist()
 
    # Level 1: exact match, ignoring case
    exact = [n for n in all_names if n.lower() == player_name.lower()]
 
    # Level 2: the typed name appears somewhere inside a real name
    # for example "Amad Diallo" matching "Amad Diallo Traore"
    contains = [n for n in all_names if player_name.lower() in n.lower()]
 
    # Level 3: no exact or substring match - suggest close spellings instead
    # handles typos/accents like "Mohamed Salah" vs "Mohammed Salah"
    close = difflib.get_close_matches(player_name, all_names, n=5, cutoff=0.6)
 
    if exact:
        resolved_name = exact[0]
    elif len(contains) == 1:
        resolved_name = contains[0]
        print(f"Interpreting '{player_name}' as '{resolved_name}'")
    elif len(contains) > 1:
        print(f"'{player_name}' matches multiple players - be more specific:")
        for n in contains:
            print(f"  - {n}")
        return None
    elif close:
        print(f"'{player_name}' not found exactly. Did you mean one of these?")
        for n in close:
            print(f"  - {n}")
        return None
    else:
        print(f"'{player_name}' not found, and no close matches either.")
        return None
 
    player_idx = df.index[df["player"] == resolved_name].tolist()[0]
 
    # Pull this player's row out of the similarity matrix - it's their
    # similarity score against every other player in the dataset
    scores = similarity_matrix[player_idx]
 
    results = df[["player", "team", "position"]].copy()
    results["similarity"] = scores
 
    # Drop the player themselves (always 1.0, not a useful "match")
    results = results[results["player"] != resolved_name]
 
    #added reset index at the end to just have it listed 1-5 instead of the default row number from pandas
    results = results.sort_values("similarity", ascending=False).head(top_n).reset_index(drop=True)
    results.index += 1
    return results


# Test, swap this name for any player in the dataset
if __name__ == "__main__":
    example = find_similar_players("amad dialo", top_n=5)

    #making column titles capitalized
    if example is not None:
        example_display = example.rename(columns={
            "player": "Player",
            "team": "Team",
            "position": "Position",
            "similarity": "Similarity",
        })
        print(example_display)
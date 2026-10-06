import difflib

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# Load the dataset that now includes market values
df = pd.read_csv("data/player_features_with_value.csv")
df["position"] = df["position"].str.replace(" S", "").str.replace("S", "")

feature_cols = [
    "goals_p90", "xg_p90", "np_xg_p90", "shots_p90",
    "assists_p90", "xa_p90", "key_passes_p90",
    "xg_chain_p90", "xg_buildup_p90",
]

X = df[feature_cols]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
similarity_matrix = cosine_similarity(X_scaled)


def resolve_player_name(player_name):
    """Same 3-level name matching as before: exact -> substring -> fuzzy.
    Returns the resolved name, or None if no confident match is found."""

    all_names = df["player"].tolist()
    exact = [n for n in all_names if n.lower() == player_name.lower()]
    contains = [n for n in all_names if player_name.lower() in n.lower()]
    close = difflib.get_close_matches(player_name, all_names, n=5, cutoff=0.6)

    if exact:
        return exact[0]
    elif len(contains) == 1:
        print(f"Interpreting '{player_name}' as '{contains[0]}'")
        return contains[0]
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


def find_cheaper_alternative(player_name, top_n=5, pool_size=50):
    """Find statistically similar players who are cheaper than the given
    benchmark player, based on market value. Casts a wide similarity net
    first (pool_size), then filters that pool down to affordable options,
    then re-sorts by similarity."""

    resolved_name = resolve_player_name(player_name)
    if resolved_name is None:
        return None

    player_idx = df.index[df["player"] == resolved_name].tolist()[0]
    benchmark_value = df.loc[player_idx, "market_value_in_eur"]

    if pd.isna(benchmark_value):
        print(f"'{resolved_name}' has no known market value - can't filter by budget.")
        return None

    # Step 1: cast a wide net on pure statistical similarity
    scores = similarity_matrix[player_idx]
    pool = df[["player", "team", "position", "market_value_in_eur"]].copy()
    pool["similarity"] = scores
    pool = pool[pool["player"] != resolved_name]
    pool = pool.sort_values("similarity", ascending=False).head(pool_size)

    # Step 2: filter that pool down to players CHEAPER than the benchmark,
    # and who actually have a known value (can't confirm "cheaper" for
    # players with missing valuations, so they're excluded here)
    affordable = pool[
        pool["market_value_in_eur"].notna()
        & (pool["market_value_in_eur"] < benchmark_value)
    ]

    if affordable.empty:
        print(f"No cheaper statistically-similar players found in the top {pool_size}.")
        return None

    # Step 3: re-sort the affordable pool by similarity, return the best few
    result = affordable.sort_values("similarity", ascending=False).head(top_n)
    result = result.reset_index(drop=True)
    result.index = result.index + 1

    print(f"\nBenchmark: {resolved_name} (€{benchmark_value:,.0f})\n")
    return result


if __name__ == "__main__":
    example = find_cheaper_alternative("Jude Bellingham", top_n=5)

    if example is not None:
        example_display = example.rename(columns={
            "player": "Player",
            "team": "Team",
            "position": "Position",
            "market_value_in_eur": "Market Value (EUR)",
            "similarity": "Similarity",
        })
        print(example_display)
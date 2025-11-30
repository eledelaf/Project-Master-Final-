import pandas as pd

CSV_PATH = "sample_texts_with_candidate_refined.csv"
df = pd.read_csv(CSV_PATH)

# Example: list of URLs whose label you want to change
urls_to_make_protest = []

urls_to_make_non_protest = ["https://www.dailymail.co.uk/news/article-9737841/The-nation-holds-breath-England-grinds-halt-Euros-clash-old-rivals-Germany.html?ns_mchannel=rss&ito=1490&ns_campaign=1490",
                            "https://www.theguardian.com/world/2020/aug/17/la-caravana-del-diablo-a-migrant-caravan-in-mexico-photo-essay",
                            "https://www.dailymail.co.uk/news/article-8509647/Goat-trim-Mountain-goats-form-orderly-queue-outside-barbers-Welsh-town.html?ns_mchannel=rss&ito=1490&ns_campaign=1490"                            
]

# Set protest = 1
df.loc[df["_id"].isin(urls_to_make_protest), "candidate_refined"] = True

# Set non-protest = 0
df.loc[df["_id"].isin(urls_to_make_non_protest), "candidate_refined"] = False

df.to_csv("sample_texts_with_candidate_refined_clean.csv", index=False)

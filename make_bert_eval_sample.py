from pymongo import MongoClient
import pandas as pd

# ---------- 0. Mongo connection ----------
Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
client = MongoClient(Mongo_uri)
db = client["ProjectMaster"]
col = db["Texts"]

# ---------- 1. How many to sample from each bucket ----------
N_HIGH_POS = 30       # BERT = 1, high confidence
N_BORDER_POS = 30     # BERT = 1, medium confidence
N_HIGH_NEG = 30       # BERT = 0, high confidence

# adjust thresholds if you like
HIGH_THRESH = 0.8
LOW_THRESH = 0.5

# ---------- 2. Helper to run an aggregation with $sample ----------
def sample_bucket(match_query, size, bucket_name):
    if size <= 0:
        return pd.DataFrame()

    pipeline = [
        {"$match": match_query},
        {"$sample": {"size": size}},
        {"$project": {
            "_id": 1,
            "title": 1,
            "text": 1,
            "bert_protest_label": 1,
            "bert_protest_score": 1,
            "url_candidate": 1,
        }},
    ]
    docs = list(col.aggregate(pipeline))
    if not docs:
        return pd.DataFrame()

    df = pd.DataFrame(docs)
    df["bucket"] = bucket_name
    return df

# Only look at docs where we actually ran BERT, and url_candidate=True
base_match = {
    "url_candidate": True,
    "bert_protest_label": {"$exists": True},
    "bert_protest_score": {"$exists": True},
}

# ---------- 3. Define buckets ----------

# High-confidence positives: label=1, score >= 0.8
df_high_pos = sample_bucket(
    {**base_match,
     "bert_protest_label": 1,
     "bert_protest_score": {"$gte": HIGH_THRESH}},
    N_HIGH_POS,
    "high_pos",
)

# Borderline positives: label=1, 0.5 <= score < 0.8
df_border_pos = sample_bucket(
    {**base_match,
     "bert_protest_label": 1,
     "bert_protest_score": {"$gte": LOW_THRESH, "$lt": HIGH_THRESH}},
    N_BORDER_POS,
    "border_pos",
)

# High-confidence negatives: label=0, score >= 0.8
df_high_neg = sample_bucket(
    {**base_match,
     "bert_protest_label": 0,
     "bert_protest_score": {"$gte": HIGH_THRESH}},
    N_HIGH_NEG,
    "high_neg",
)

# ---------- 4. Concatenate and export ----------

df_all = pd.concat([df_high_pos, df_border_pos, df_high_neg], ignore_index=True)

# Add empty column for your manual coding
df_all["human_label"] = ""   # you will fill 1 or 0

out_path = "bert_posthoc_sample.csv"
df_all.to_csv(out_path, index=False, encoding="utf-8")

print(f"Saved sample of {len(df_all)} docs to {out_path}")
print(df_all[["bucket", "bert_protest_label", "bert_protest_score"]].head())
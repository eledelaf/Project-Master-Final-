from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
import re

"""
Pre-filter for possible protest articles using two levels:

  1) URL filter:
       url_candidate = False   if URL starts with one of the EXCLUDED_URL_PREFIXES
       url_candidate = True    otherwise

  2) Text keywords (only if url_candidate = True):
       keyword_candidate = True  if protest terms in title/text
       keyword_candidate = False otherwise
"""

# --- 1. Keyword-based text filter ---

PROTEST_TERMS = [
    "protest", "protests", "protester", "protesters",
    "demonstration", "demonstrations", "demo",
    "rally", "march", "sit-in", "occupation",
    "blockade", "strike", "walkout", "picket", "picket line",
    "riot", "riots",
    "clash with police", "clashes with police",
    "took to the streets", "mass protest", "mass demonstration"
]

text_pattern = re.compile(
    "|".join(re.escape(t) for t in PROTEST_TERMS),
    re.IGNORECASE
)

# --- 2. Mongo connection ---

Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
client = MongoClient(Mongo_uri)
db = client["ProjectMaster"]
col = db["Texts"]

batch_size = 500
cursor = col.find({}, {"_id": 1, "title": 1, "text": 1})

batch = []

for doc in cursor:
    url = str(doc.get("_id", ""))   # _id is your URL (string)
    title = doc.get("title") or ""
    text = doc.get("text") or ""

    # 1) Keyword filter 
    full_text = title + " " + text
    keyword_candidate = bool(text_pattern.search(full_text))

    batch.append(
        UpdateOne(
            {"_id": doc["_id"]},
            {"keyword_candidate": keyword_candidate} # He cambiado esto pero no se si esta bien 
        )
    )

    if len(batch) >= batch_size:
        try:
            col.bulk_write(batch)
        except PyMongoError as e:
            print("Mongo error in bulk_write:", e)
        batch = []

# Flush remaining operations
if batch:
    try:
        col.bulk_write(batch)
    except PyMongoError as e:
        print("Mongo error in final bulk_write:", e)

print("Finished updating url_candidate and keyword_candidate.")

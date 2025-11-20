from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
import re

"""
Pre-filter for possible protest articles using:
  1) URL: if URL starts with one of the excluded section prefixes -> keyword_candidate = False
  2) Text keywords: only applied if URL is not excluded.
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

# --- 2. URL prefixes to always exclude ---

EXCLUDED_URL_PREFIXES = [
    # Daily Mail
    "https://www.dailymail.co.uk/news/royals",
    "https://www.dailymail.co.uk/sport",
    "https://www.dailymail.co.uk/tvshowbiz",
    "https://www.dailymail.co.uk/lifestyle",
    "https://www.dailymail.co.uk/health",
    "https://www.dailymail.co.uk/travel",
    "https://www.dailymail.co.uk/buyline",
    "https://www.dailymail.co.uk/femail",

    # The Guardian
    "https://www.theguardian.com/uk/commentisfree",
    "https://www.theguardian.com/commentisfree",
    "https://www.theguardian.com/uk/sport",
    "https://www.theguardian.com/sports",
    "https://www.theguardian.com/uk/culture",
    "https://www.theguardian.com/culture",
    "https://www.theguardian.com/uk/lifeandstyle",
    "https://www.theguardian.com/lifeandstyle",
    "https://www.theguardian.com/music",

    # Evening Standard
    "https://www.standard.co.uk/sport",
    "https://www.standard.co.uk/lifestyle",
    "https://www.standard.co.uk/culture",
    "https://www.standard.co.uk/going-out",
    "https://www.standard.co.uk/homesandproperty",
    "https://www.standard.co.uk/comment"
    
]
# "https://www.theguardian.com/uk/commentisfree", no lo esta cogiendo bien
# "https://www.dailymail.co.uk/stage


NON_PROTEST_URL_REGEX = re.compile(
    r"^(?:" + "|".join(re.escape(p) for p in EXCLUDED_URL_PREFIXES) + r")"
)

# --- 3. Mongo connection ---

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

    # 1) URL filter: if URL starts with one of the excluded prefixes -> directly False
    if NON_PROTEST_URL_REGEX.match(url):
        is_candidate = False
    else:
        # 2) URL is acceptable -> check text for protest keywords
        full_text = title + " " + text
        is_candidate = bool(text_pattern.search(full_text))

    batch.append(
        UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {"keyword_candidate": is_candidate}}
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

print("Finished updating keyword_candidate.")

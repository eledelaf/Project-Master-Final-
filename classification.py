from pymongo import MongoClient
import re

from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError


"""
In this file we are going to do the classification model
"""

# First I am going to do a pre-filter with some more key words to have a group of possible articles 
# that are more likely to be protest related. 
# To do that we are going to have a list of words that are more likely to be at an article about a protest

PROTEST_TERMS = ["protest", "protests", "protester", "protesters","demonstration", 
                 "demonstrations", "demo","rally", "march", "sit-in", "occupation", 
                 "blockade", "strike", "walkout", "picket", "picket line", "riot", 
                 "riots", "clash with police", "clashes with police", 
                 "took to the streets", "mass protest", "mass demonstration"]

# https://www.geeksforgeeks.org/mongodb/search-text-in-mongodb/



Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
client = MongoClient(Mongo_uri)
db = client["ProjectMaster"]
col = db["Texts"]

# precompile regex
pattern = re.compile("|".join(re.escape(t) for t in PROTEST_TERMS), re.IGNORECASE)

batch_size = 500
cursor = col.find({}, {"_id": 1, "title": 1, "text": 1})

batch = []
for doc in cursor:
    text = (doc.get("title") or "") + " " + (doc.get("text") or "")
    is_candidate = bool(pattern.search(text))
    batch.append(
        {
            "filter": {"_id": doc["_id"]},
            "update": {"$set": {"keyword_candidate": is_candidate}}
        }
    )
    if len(batch) == batch_size:
        col.bulk_write([ 
            UpdateOne(b["filter"], b["update"]) for b in batch 
        ])
        batch = []

if batch:
    col.bulk_write([UpdateOne(b["filter"], b["update"]) for b in batch])

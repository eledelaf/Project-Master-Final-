import pandas as pd
from pymongo import MongoClient

# 1. Connect to Mongo
client = MongoClient(
    "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
)
db = client["ProjectMaster"]
col = db["sample_texts"]

# 2. Get all documents from the collection
docs = list(col.find({}))   # {} = no filter -> all docs

# 3. Put them into a DataFrame
df = pd.DataFrame(docs)

# 4. Make _id a string (URLs / ObjectId -> string)
df["_id"] = df["_id"].astype(str)

# 5. Save to CSV
df.to_csv("sample_texts.csv", index=False)

print(f"Exported {len(df)} rows to sample_texts.csv")

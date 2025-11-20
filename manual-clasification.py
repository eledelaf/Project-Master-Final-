from pymongo import MongoClient
from bson.objectid import ObjectId

Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
client = MongoClient(Mongo_uri)
db = client["ProjectMaster"]

source = db["Texts"]                       # original collection
sample = db["sample_texts"] 

# --- 1. Sample  ---
N_CANDIDATES = 500
N_NON_CANDIDATES = 300

# --- 1. Count how many candidate / non-candidate docs you actually have ---
n_candidates_total = source.count_documents({"keyword_candidate": True})
n_non_candidates_total = source.count_documents({"keyword_candidate": False})

n_candidates = min(N_CANDIDATES, n_candidates_total)
n_non_candidates = min(N_NON_CANDIDATES, n_non_candidates_total)

print(f"Total candidate docs in source: {n_candidates_total}")
print(f"Total non-candidate docs in source: {n_non_candidates_total}")
print(f"Sampling {n_candidates} candidates and {n_non_candidates} non-candidates.")

# --- 2. Sample from source collection using aggregation + $sample ---

# Sample candidate docs
candidate_docs = list(source.aggregate([
    {"$match": {"keyword_candidate": True}},
    {"$sample": {"size": n_candidates}},
    {"$project": {"_id": 1, "title": 1, "keyword_candidate": 1}}
]))

# Sample non-candidate docs
non_candidate_docs = list(source.aggregate([
    {"$match": {"keyword_candidate": False}},
    {"$sample": {"size": n_non_candidates}},
    {"$project": {"_id": 1, "title": 1, "keyword_candidate": 1}}
]))

all_docs = candidate_docs + non_candidate_docs
print("Total sampled docs:", len(all_docs))

# --- 3. Insert into sample collection (without overwriting existing labels) ---

for d in all_docs:
    doc_to_insert = {
        "_id": d["_id"],  # same URL as id
        "title": d.get("title", ""),
        "keyword_candidate": bool(d.get("keyword_candidate", False)),
        # you will manually set this to True/False later
        "candidate": None
    }

    # $setOnInsert ensures we only insert if it doesn't exist yet
    sample.update_one(
        {"_id": doc_to_insert["_id"]},
        {"$setOnInsert": doc_to_insert},
        upsert=True
    )

print("Finished creating/updating sample in collection")
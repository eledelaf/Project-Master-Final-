from pymongo import MongoClient
from bson.objectid import ObjectId

Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
client = MongoClient(Mongo_uri)
db = client["ProjectMaster"]

source = db["Texts"]         # original collection
sample = db["sample_texts"] 

# --- 1. Target sample sizes ---
N_CANDIDATES = 350        # positives (keyword_candidate=True, url_candidate=True)
N_NON_CANDIDATES = 150    # negatives (keyword_candidate=False, url_candidate=True)

# --- 2. Count how many candidate / non-candidate docs you actually have ---
# Only consider docs with url_candidate = True

n_candidates_total = source.count_documents({
    "keyword_candidate": True,
    "url_candidate": True
})

n_non_candidates_total = source.count_documents({
    "keyword_candidate": False,
    "url_candidate": True
})

n_candidates = min(N_CANDIDATES, n_candidates_total)
n_non_candidates = min(N_NON_CANDIDATES, n_non_candidates_total)

print(f"Total candidate docs in source (kw=True, url=True): {n_candidates_total}")
print(f"Total non-candidate docs in source (kw=False, url=True): {n_non_candidates_total}")
print(f"Sampling {n_candidates} candidates and {n_non_candidates} non-candidates.")

# --- 3. Sample from source collection using aggregation + $sample ---

# Sample positive (candidate) docs
candidate_docs = list(source.aggregate([
    {"$match": {"keyword_candidate": True, "url_candidate": True}},
    {"$sample": {"size": n_candidates}},
    {"$project": {
        "_id": 1,
        "title": 1,
        "keyword_candidate": 1,
        "url_candidate": 1,
        "text": 1
    }}
]))

# Sample negative (non-candidate) docs
non_candidate_docs = list(source.aggregate([
    {"$match": {"keyword_candidate": False, "url_candidate": True}},
    {"$sample": {"size": n_non_candidates}},
    {"$project": {
        "_id": 1,
        "title": 1,
        "keyword_candidate": 1,
        "url_candidate": 1,
        "text": 1
    }}
]))

all_docs = candidate_docs + non_candidate_docs
print("Total sampled docs:", len(all_docs))

# --- 4. Insert into sample collection ---

for d in all_docs:
    # candidate label according to your rule:
    # True  if keyword_candidate=True AND url_candidate=True
    # False if keyword_candidate=False AND url_candidate=True
    # (we are only sampling url_candidate=True anyway)
    kw = bool(d.get("keyword_candidate", False))
    url_ok = bool(d.get("url_candidate", False))
    candidate_label = kw and url_ok

    doc_to_insert = {
        "_id": d["_id"],  # same URL as id
        "title": d.get("title", ""),
        "candidate": candidate_label,   # <-- this is now True/False, not None
        "text": d.get("text", "")
    }

    # $setOnInsert ensures we only insert if it doesn't exist yet
    sample.update_one(
        {"_id": doc_to_insert["_id"]},
        {"$setOnInsert": doc_to_insert},
        upsert=True
    )

print("Finished creating/updating sample in collection")

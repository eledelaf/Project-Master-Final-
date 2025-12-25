#!/usr/bin/env python3
"""
clean_mongo_fields.py

Replaces each document in a MongoDB collection with ONLY the fields you want to keep.
This effectively deletes all other fields (hf_*, sentiment, paper, etc.) in one go.

Works best with MongoDB 4.2+ using $project + $merge.
If $merge is not permitted, it falls back to a batched ReplaceOne loop.

USAGE:
  python clean_mongo_fields.py
"""

from pymongo import MongoClient, ReplaceOne
from pymongo.errors import OperationFailure
from datetime import datetime

# ----------------------------
# CONFIG (EDIT THIS)
# ----------------------------
MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
DB_NAME = "ProjectMaster"
#COLLECTION_NAME = "Texts"
COLLECTION_NAME = "sample_texts"


# Keep ONLY these fields in the collection (everything else is removed)
"""
KEEP_FIELDS = [
    "_id",
    "publish_date",
    "status",
    "time_enqueued",
    "title",
    "text",
    "time_scraped",
    "paper",  
]
"""
KEEP_FIELDS = [
    "_id",
    "title",
    "text",
    "human_label",
    "hf_confidence",
    "hf_label",
    "hf_label_name",
    "hf_model",
    "hf_reason",
    "hf_status",
]


# Optional: make a backup copy collection first (recommended)
#MAKE_BACKUP = True
MAKE_BACKUP = False
BACKUP_SUFFIX = "_backup_before_clean"  # collection will be: COLLECTION_NAME + suffix

# If fallback loop is used:
BATCH_SIZE = 1000

# ----------------------------
# SCRIPT
# ----------------------------
def backup_collection(db, source_name: str, backup_name: str) -> None:
    """Create a backup collection using aggregation $out."""
    print(f"[backup] Creating backup collection: {backup_name}")
    db[source_name].aggregate(
        [{"$match": {}}, {"$out": backup_name}],
        allowDiskUse=True
    )
    print("[backup] Done.")


def clean_with_merge(db, coll_name: str, keep_fields: list[str]) -> None:
    """
    Preferred method: server-side $project + $merge (replaces docs in-place).
    """
    proj = {k: 1 for k in keep_fields}
    pipeline = [
        {"$project": proj},
        {
            "$merge": {
                "into": coll_name,
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "discard",
            }
        }
    ]
    print("[clean] Trying server-side $project + $merge (fastest)...")
    db[coll_name].aggregate(pipeline, allowDiskUse=True)
    print("[clean] Done via $merge.")


def clean_with_replace_loop(db, coll_name: str, keep_fields: list[str], batch_size: int = 1000) -> None:
    """
    Fallback method if $merge is not allowed: fetch projected docs and ReplaceOne in batches.
    """
    coll = db[coll_name]
    projection = {k: 1 for k in keep_fields}
    total = coll.count_documents({})
    print(f"[clean] Falling back to ReplaceOne loop. Documents: {total}")

    ops = []
    processed = 0
    cursor = coll.find({}, projection=projection, no_cursor_timeout=True)

    try:
        for doc in cursor:
            # doc already contains only projected fields (+ _id)
            ops.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=False))

            if len(ops) >= batch_size:
                coll.bulk_write(ops, ordered=False)
                processed += len(ops)
                ops = []
                print(f"[clean] Processed {processed}/{total}")

        if ops:
            coll.bulk_write(ops, ordered=False)
            processed += len(ops)
            print(f"[clean] Processed {processed}/{total}")

    finally:
        cursor.close()

    print("[clean] Done via ReplaceOne loop.")


def main() -> None:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Backup first (optional but smart)
    if MAKE_BACKUP:
        backup_name = f"{COLLECTION_NAME}{BACKUP_SUFFIX}"
        # Avoid overwriting an existing backup
        if backup_name in db.list_collection_names():
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{backup_name}_{stamp}"
        backup_collection(db, COLLECTION_NAME, backup_name)

    # Try fast in-place clean with $merge, fallback if not allowed
    try:
        clean_with_merge(db, COLLECTION_NAME, KEEP_FIELDS)
    except OperationFailure as e:
        print(f"[warn] $merge failed (likely permissions/cluster version). Error: {e}")
        clean_with_replace_loop(db, COLLECTION_NAME, KEEP_FIELDS, batch_size=BATCH_SIZE)

    print("\nAll done.")
    print(f"Collection '{COLLECTION_NAME}' now contains ONLY: {KEEP_FIELDS}")


if __name__ == "__main__":
    main()

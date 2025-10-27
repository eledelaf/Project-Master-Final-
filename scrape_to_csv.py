import pandas as pd
import concurrent.futures
import time
import random

from datetime import datetime, timezone
from fun_scraple import scrape_and_text  # Scrapping function
from tqdm import tqdm  # For a nice progress bar
from pymongo.mongo_client import MongoClient # To connect to mongo
from pymongo.errors import PyMongoError
from pymongo import UpdateOne

"""
This script takes the URLS_clean.csv file, scrapes the content using
multi-threading, and updates the text into mongoDB.
"""

# --- 0.1 Configuration ---
MAX_WORKERS = 8  # Number of threads. Adjust based on your network/CPU.
INPUT_FILE = "URLS_clean.csv"

# --- 0.2 Connection to Mongo ---
Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
client = MongoClient(Mongo_uri)
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
        print(e)    

db = client["ProjectMaster"] # Data base
coll_texts = db["Texts"] # Here is where I am going to upload the Texts after the scrapping


# --- 1. Worker Function ---
def process_url(index, url, title):
    """
    Worker function for each thread.
    Scrapes a single URL and returns the index, text, and timestamp.
    """

    try:
        # This makes requests look less robotic and avoids 429 errors
        time.sleep(random.uniform(0.5, 2.5))

        # We pass (url, title) 
        text = scrape_and_text(url, title)
        timestamp = datetime.now()
        
        if text is None:  # Handle case where scrape_and_text fails 
            return index, "SCRAPE_FAILED", timestamp
            
        return index, text, timestamp
    except Exception as e:
        # Catch any other unexpected errors
        print(f"\nUnexpected error in worker for index {index} ({url}): {e}")
        return index, f"WORKER_ERROR: {e}", datetime.now()


# --- 2. Load and Prepare Data ---
print(f"Loading data from {INPUT_FILE}...")
try:
    df = pd.read_csv(INPUT_FILE, sep=";")
except FileNotFoundError:
    print(f"Error: {INPUT_FILE} not found. Please make sure it's in the same directory.")
    exit()

df_1 = df[['id', 'publish_date', 'title', 'url']].copy()


# Clean URLs and drop duplicates
df_1['url'] = df_1['url'].astype(str).str.strip()
df_1 = df_1[df_1['url'].str.startswith('http')]
df_1 = df_1.drop_duplicates(subset=['url'])


# --- 3. Check in MONGO if that URL is been used already ---
def ensure_indexes():
    coll_texts.create_index("status")
    coll_texts.create_index("publish_date")
ensure_indexes()

# --- 3.1 Build a set of known URLs from Mongo in order to skip them ---
known_ids = {d["_id"] for d in coll_texts.find({}, {"_id": 1}) if isinstance(d.get("_id"), str)}
known_urls = {d.get("url") for d in coll_texts.find({"url": {"$type": "string"}}, {"url": 1})}
already_in_mongo = known_ids | {u for u in known_urls if u}
print(f"Mongo already has {len(already_in_mongo)} URLs.")

# Get a list of rows that still need to be scraped
# We use .iterrows() which gives (index, Series)
# We need the *dataframe index* (like 0, 1, 5, 10) to use .loc later

rows_to_scrape = [(idx, row["url"], row["title"])
                for idx, row in df_1.iterrows()
                if row["url"] not in already_in_mongo]
print(f"To scrape now: {len(rows_to_scrape)} (out of {len(df_1)})")

if not rows_to_scrape:
    print("Nothing to scrape. Exiting.")
    exit(0)


# --- 4. Scrapping with ThreadPoolExecutor ---
def update_collection(collection, data:dict):
    if "_id" in data:
        flt = {"_id": data["_id"]}
    elif "url" in data:
        flt = {"url": data["url"]}
    else:
        raise ValueError("data must contain '_id' or 'url' for a safe upsert")
    collection.update_one(flt, {"$set": data}, upsert=True)

# OPTIONAL: seed 'pending' documents for observability in Mongo UI
now_utc = datetime.now(timezone.utc)
seed_ops = []
for idx, url, title in rows_to_scrape:
    pub = df_1.loc[idx, "publish_date"]
    seed_ops.append(
        UpdateOne({"_id": url},
                  {"$setOnInsert": {
                      "_id": url,
                      "url": url,
                      "title": title,
                      "publish_date": pub,
                      "status": "pending",
                      "time_enqueued": now_utc
                  }},
                  upsert=True)
    )
if seed_ops:
    try:
        coll_texts.bulk_write(seed_ops, ordered=False)
    except PyMongoError as e:
        print(f"Seeding warning: {e}")

print(f"Starting scrape with {MAX_WORKERS} workers...")
total_to_scrape = len(rows_to_scrape)
ok = failed = err = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # submit jobs
    futures = {
        executor.submit(process_url, idx, url, title): (idx, url, title)
        for (idx, url, title) in rows_to_scrape
    }
   
    for future in tqdm(concurrent.futures.as_completed(futures),
                       total=total_to_scrape, desc="Scraping URLs"):
        idx, url, title = futures[future]
        publish_date = df_1.loc[idx, "publish_date"]

        try:
            _index, text, timestamp = future.result()

            if text == "SCRAPE_FAILED":
                update_collection(coll_texts, {
                    "_id": url,
                    "status": "failed",
                    "error": "SCRAPE_FAILED",
                    "time_scraped": timestamp
                })
                failed += 1
            elif isinstance(text, str) and len(text) > 0:
                update_collection(coll_texts, {
                    "_id": url,
                    "url": url,
                    "title": title,
                    "publish_date": publish_date,
                    "text": text,
                    "status": "done",
                    "time_scraped": timestamp
                })
                ok += 1
            else:
                update_collection(coll_texts, {
                    "_id": url,
                    "status": "failed",
                    "error": "EMPTY_TEXT",
                    "time_scraped": timestamp
                })
                failed += 1

        except Exception as e:
            update_collection(coll_texts, {
                "_id": url,
                "status": "error",
                "error": f"{type(e).__name__}: {e}",
                "time_scraped": datetime.now(timezone.utc)
            })
            err += 1

print(f"Finished. ok={ok} failed={failed} error={err}")

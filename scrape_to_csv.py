import pandas as pd
import concurrent.futures
import time
import random
import os  # Needed for file check

from datetime import datetime, timezone
from fun_scraple import scrape_and_text  # Scrapping function
from tqdm import tqdm  # For a nice progress bar
from pymongo.mongo_client import MongoClient # To connect to mongo
from pymongo.server_api import ServerApi
from pymongo.errors import PyMongoError

"""
This script takes the URLS_clean.csv file, scrapes the content using
multi-threading, and updates the text into mongoDB.
"""

# --- 0.1 Configuration ---
MAX_WORKERS = 8  # Number of threads. Adjust based on your network/CPU.
SAVE_INTERVAL = 100  # Save a checkpoint every N URLs
INPUT_FILE = "URLS_clean.csv"
FINAL_NAME = 'ScrapedDataFinal' # This is the name of the db on mongo where we are going to upload the texts

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

rows_to_scrape = [(idx, row["url"], row["title"])
                for idx, row in df_1.iterrows()
                if row["url"] not in already_in_mongo]
print(f"To scrape now: {len(rows_to_scrape)} (out of {len(df_1)})")

"""
# --- 4. Scrapping with ThreadPoolExecutor ---
print(f"Starting scrape with {MAX_WORKERS} workers...")

# Get a list of rows that still need to be scraped
# We use .iterrows() which gives (index, Series)
# We need the *dataframe index* (like 0, 1, 5, 10) to use .loc later
rows_to_scrape = [
    (index, row['url'], row['title'])
    for index, row in df_1.iterrows()
    if pd.isna(row['text'])
]

total_to_scrape = len(rows_to_scrape)

if total_to_scrape == 0:
    print("All URLs already scraped according to checkpoint.")
else:
    print(f"Total URLs to scrape: {total_to_scrape} (out of {len(df_1)} total)")

    completed_count = 0
    
    # We use a context manager to ensure threads are cleaned up properly
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        # Submit all jobs to the executor.
        # We map 'futures' to the original dataframe index
        future_to_index = {
            executor.submit(process_url, index, url, title): index
            for (index, url, title) in rows_to_scrape
        }
        
        # Use as_completed to get results as soon as they are done
        # Wrap with tqdm for a progress bar
        for future in tqdm(concurrent.futures.as_completed(future_to_index), total=total_to_scrape, desc="Scraping URLs"):
            index = future_to_index[future]  # Get the original dataframe index
            
            try:
                # Get the result from the thread
                _index, text, timestamp = future.result()
                
                # Update the main dataframe using the original index
                # .loc is the correct way to assign this
                df_1.loc[index, 'text'] = text
                df_1.loc[index, 'time scrapped'] = timestamp
                
                completed_count += 1
                
                # Save checkpoint
                if completed_count % SAVE_INTERVAL == 0:
                    print(f"\nCheckpoint: Saving progress ({completed_count}/{total_to_scrape})...")
                    df_1.to_csv(CHECKPOINT_FILE, index=False, sep=';') ### QUITAR EL CHECKPOINT
                    
            except Exception as e:
                # Handle errors from the future.result() call itself
                print(f"\nError processing future for index {index}: {e}")
                df_1.loc[index, 'text'] = "FUTURE_ERROR"
                df_1.loc[index, 'time scrapped'] = datetime.now()

# --- 5. Final Save ---
print("\nScraping complete. Saving final file...")
df_1.to_csv(FINAL_NAME, index=False, sep=';')

print(f"All done! Results saved to {FINAL_NAME}")
if os.path.exists(CHECKPOINT_FILE):
    print(f"Checkpoint file {CHECKPOINT_FILE} can be deleted if no longer needed.")
"""
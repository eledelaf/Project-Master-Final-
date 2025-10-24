import warnings
# Silence the specific urllib3 warning (optional; see notes below)
try:
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
except Exception:
    pass

import pandas as pd
from datetime import datetime
from fun_scraple import scrape_and_text

"""
This script reads URLS_clean.csv, scrapes article text for a small sample,
and writes sample.csv with the results.
"""

# 1) Load and select columns
df = pd.read_csv("URLS_clean.csv", sep=";")
df_1 = df[['id', 'publish_date', 'title', 'url']].copy()

# 1.1) Clean URLs and drop exact duplicates (by URL)
df_1['url'] = df_1['url'].astype(str).str.strip()
df_1 = df_1[df_1['url'].str.startswith('http')].drop_duplicates(subset=['url']).reset_index(drop=True)

# 2) Create output columns with explicit dtypes
df_1['time scrapped'] = pd.NaT          # datetime column
df_1['text'] = pd.Series(dtype='object') # text column

# 3) Scraping: first 5 rows as a sample
for i, row in df_1.head(5).iterrows():
    url = row['url']
    title = row['title']
    try:
        text = scrape_and_text(url, title)
    except Exception as e:
        # If your scraper can raise, don't crash the loop—record the error
        text = f"[SCRAPE_ERROR] {type(e).__name__}: {e}"

    # Use .loc to avoid chained-assignment warnings and set row-wise timestamp
    df_1.loc[i, 'text'] = text
    df_1.loc[i, 'time scrapped'] = datetime.now()

# 4) Save
df_1.to_csv('sample1.csv', index=False)

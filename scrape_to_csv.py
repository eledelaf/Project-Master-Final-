
import pandas as pd
from datetime import datetime
from fun_scraple import scrape_and_text
"""
This document is going to take the URLS_clean.csv file, do the scrapping and
create a new csv file with the scrapping
"""
# 1. Load input and pick required columns
df = pd.read_csv("URLS_clean.csv", sep = ";")
df_1 = df[['id', 'publish_date', 'title', 'url']].copy()

# 1.1 Clean URLs and drop exact duplicates
df_1['url'] = df_1['url'].astype(str).str.strip()
df_1 = df_1[df_1['url'].str.startswith('http')]
df_1 = df_1.drop_duplicates(subset=['url'])

# 2. Create the output columns, empty to start
df_1[['time scrapped', 'text']] = pd.NA # Created the columns 

# 3. Scrapping
# I am going to try with the column url and the first 5 rows



# Lets get the first url and get the text 
# Just a sample 
for i in range(5):
    url = df_1.loc['url', i]
    title = df_1.loc['title', i]
    df_1['text'][i] = scrape_and_text(url, title)
    df_1['time scrapped'] = datetime.now()
df_1.to_csv('sample.csv', index = False)




# Now we are going to fill up the df_1 and convert it into a csv after
import pandas as pd
import time
"""
This document is going to take the URLS_clean.csv file, do the scrapping and
create a new csv file with the scrapping
"""

df = pd.read_csv("URLS_clean.csv", sep = ";")
# print (df.columns) = ['Unnamed: 0', 'id', 'media_url', 'publish_date', 'title', 'url']
# The column 'Unnamed:0' is not necesary

df_1 = df[['id', 'publish_date', 'title', 'url']].copy()

# In the df_1 we are going to add the scrapping and a time stamp
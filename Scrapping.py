import pandas as pd

import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import re 

file_path = "/Users/elenadelafuente/Desktop/MASTER/TFM/Project/Project-Master/URLS_clean.csv"
df = pd.read_csv(file_path, sep=';')
print(df.head)
dfurl = df["url"]
url = str(dfurl.get(0))
print(url)

"""
with urlopen(url) as response:
    soup = BeautifulSoup(response, "html.parser")
    for anchor in soup.find_all("a"):
        print(anchor.get("href", "/"))
"""
import pandas as pd

import requests
from bs4 import BeautifulSoup
import pandas as pd

file_path = "/Users/elenadelafuente/Desktop/MASTER/TFM/Project/Project-Master/URLS_clean.csv"
df = pd.read_csv(file_path, sep=';')
print(df.head)
dfurl = df["url"]
url = dfurl.get(0)



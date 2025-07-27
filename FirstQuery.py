import pandas as pd 

# Upload the data set of URLS
df = pd.read_csv("/Users/elenadelafuente/Desktop/MASTER/TFM/Project/Project-Master/URLS.csv", sep = ';')  # or pd.read_csv("converted_file.csv")
print(df.head())

# We are only interested in this papers: theguardian.com, 
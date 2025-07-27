import pandas as pd 

# Upload the data set of URLS
file_path = "/Users/elenadelafuente/Desktop/MASTER/TFM/Project/Project-Master/URLS.csv"
df = pd.read_csv(file_path, sep=';', skiprows=1, header=None)
df = df.iloc[1:].reset_index(drop=True)
header = [
    "id", "indexed_date", "language", "media_name", "media_url", 
    "publish_date", "title", "url"
]
df.columns = header
print(df)
# We are only interested in this papers: The times, The Guardian, The telegraph
# Lets see which are the mediar_urls
conteo = df["media_url"].value_counts()
repetidos = conteo[conteo > 100]
print(repetidos)

# No aparece the times(conservador), asi que tengo que buscar otro periodico que sea de la misma mentalidad
# theguardian.com, telegraph.co.uk, 

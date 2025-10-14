
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from fun_scraple import scrape_and_text
import time

uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
def first(collection):
    #Devuelve el titulo y el url del primer elemento de una collecion de mongo
    target_dict = collection.find_one()
    print(type(target_dict)) # Dict
    print(target_dict) # {'_id': ObjectId('68c884685e53157e3ed0a311'), 'id': '6...3', ... , 'title': str, 'url': str}
    target_url = target_dict["url"]
    target_title = target_dict["title"]
    target_id = target_dict["_id"]
    return(target_url, target_title, target_id)

def bucle_urls(collection):
    # bucle para conseguir todos los urls
        # Tengo que ver si puedo hacer esto con programación paralela
        for x in collection.find({}, {"url": 1, "title": 1}):
            # x es un dicionario de este estilo: {'_id': ObjectId('68c884765e53157e3ed0e2e8'), 'url': str, "title": str}
            print(x)
    

def update_in_col(collection, data: dict, db_name = "URLS"):
    # Saves the data if the id is not already in the collection
    if "_id" in data:
        filter = {"_id": data["_id"]}
    elif "url" in data:
        filter = {"url": data["url"]}
    else:
        raise ValueError("data must contain '_id' or 'url' for a safe upsert")
    
    result = collection.update_one(filter, {"$set":data}, upsert=True)
    if result.upserted_id:
        print("Inserted new doc")
    else:
        print("Updated existing")
    
if __name__ == "__main__":
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        # Data base
        db = client["URLS"]
        # Colección
        collection = db["Primer Querys"]
        coll_texts = db["Texts"]
        print(bucle_urls(collection))
        
        #Devuelve el primer elemento de la colección
        target_url, target_title, target_id = first(collection)
        target_text = scrape_and_text(target_url, target_title) # STR
        
        # Crear un diccionario con los elementos que quiero 
        target_dict = {"_id": target_id, "url": target_url, "title": target_title, "text": target_text, "time_scrapped": time.time()}
        #print(target_dict)
        #print(collection.find_one())
        update_in_col(coll_texts, target_dict)

        
    except Exception as e:
        print(e)

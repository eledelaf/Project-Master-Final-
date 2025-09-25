
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"

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
    """
    #Devuelve el primer elemento de la colección
    x = collection.find_one()
    print(type(x)) 
    """
    # bucle para conseguir todos los urls
    # Tengo que ver si puedo hacer esto con programación paralela
    for x in collection.find({}, {"url": 1 }):
        # x es un dicionario de este estilo: {'_id': ObjectId('68c884765e53157e3ed0e2e8'), 'url': str}
        print(x) 
    
   

except Exception as e:
    print(e)


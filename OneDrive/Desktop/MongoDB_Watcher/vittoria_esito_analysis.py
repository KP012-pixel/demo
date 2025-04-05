import pymongo
import os
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = "mongodb+srv://Kritika:Gungun%40012@cluster0.jmgoo6y.mongodb.net/legal_db"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client["legal_db"]
collection = db["cases"]

pipeline = [
    {
        "$group": {
            "_id": {
                "autorità": "$autorità",
                "esito": "$fatto.primo_grado.esito.vittoria.esito"
            },
            "count": {"$sum": 1}
        }
    },
    {
        "$sort": {"count": -1}
    }
]

results = list(collection.aggregate(pipeline))

# Store results in a new collection
results_collection = db["vittoria_esito_counts"]
results_collection.delete_many({})  # Clear previous results
for result in results:
    results_collection.insert_one(result)
    print(f"Autorità: {result['_id']['autorità']}, Esito: {result['_id']['esito']}, Count: {result['count']}")

print("Vittoria esito counts stored in 'vittoria_esito_counts' collection.")

client.close()
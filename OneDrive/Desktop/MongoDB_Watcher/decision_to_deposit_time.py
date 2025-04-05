import pymongo
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = "mongodb+srv://Kritika:Gungun%40012@cluster0.jmgoo6y.mongodb.net/legal_db"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client["legal_db"]
collection = db["cases"]

pipeline = [
    {
        "$project": {
            "_id": 1,
            "deposito": "$date.deposito.valore",
            "decisione": "$date.decisione.valore"
        }
    },
    {
        "$match": {
            "deposito": {"$ne": None},
            "decisione": {"$ne": None}
        }
    }
]

results = list(collection.aggregate(pipeline))

# Store results in a new collection
results_collection = db["decision_to_deposit_time"]
results_collection.delete_many({})  # Clear previous results

for result in results:
    deposito_str = result["deposito"]
    decisione_str = result["decisione"]

    try:
        deposito_date = datetime.strptime(deposito_str, "%Y-%m-%d")
        decisione_date = datetime.strptime(decisione_str, "%Y-%m-%d")

        duration = deposito_date - decisione_date  # Corrected subtraction, no order change
        total_days = duration.days

        results_collection.insert_one(
            {
                "_id": result["_id"],
                "days": total_days,
            }
        )
        print(f"ID: {result['_id']}, Days: {total_days}")
    except ValueError as e:
        print(f"Error processing ID: {result['_id']}: {e}")

print("Decision-to-deposit times stored in 'decision_to_deposit_time' collection.")

client.close()
import pymongo
import json
import os
import time
import watchdog.events
import watchdog.observers

# MongoDB Atlas connection string (without the password)
CONNECTION_STRING = "mongodb+srv://Kritika:Gungun%40012@cluster0.jmgoo6y.mongodb.net/legal_db"

# Directory to monitor
WATCH_DIRECTORY = "C:\\Users\\kriti\\OneDrive\\Desktop\\MongoDB_Watcher\\JSON_Files"

def insert_json_to_mongodb(filepath):
    """Inserts a JSON file into MongoDB."""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)

        password = os.environ.get("MONGODB_PASSWORD")
        connection_string = CONNECTION_STRING.format(password=password)

        client = pymongo.MongoClient(connection_string)
        db = client["legal_db"]
        collection = db["cases"]
        collection.insert_one(data)
        print(f"Inserted {filepath} into MongoDB.")
        client.close()
    except Exception as e:
        print(f"Error inserting {filepath}: {e}")

class FileEventHandler(watchdog.events.FileSystemEventHandler):
    """Handles file creation events."""
    def on_created(self, event):
        if event.is_directory:
            return None
        elif event.src_path.endswith(".json"):
            insert_json_to_mongodb(event.src_path)

def process_existing_files(directory):
    """Processes JSON files that are already in the directory."""
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            insert_json_to_mongodb(filepath)

if __name__ == "__main__":
    # Process existing files first
    process_existing_files(WATCH_DIRECTORY)

    event_handler = FileEventHandler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
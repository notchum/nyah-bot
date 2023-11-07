import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

print(f"Database URI: {os.getenv('DATABASE_URI')}")
client = MongoClient(os.getenv("DATABASE_URI"))
print("Connected to MongoDB Atlas!")
db = client['nyah']
collection = db['players']
print(f"Collection name: {db.name}.{collection.name}")

filter = {}
update = {"$set": {"inventory": []}}

result = collection.update_many(filter, update)
print(f"Number of documents matched: {result.matched_count}")
print(f"Number of documents modified: {result.modified_count}")

import os
import sys
import uuid

from dotenv import load_dotenv
from pymongo import MongoClient
import bson

load_dotenv()

print(f"Database URI: {os.getenv('DATABASE_URI')}")
client = MongoClient(os.getenv("DATABASE_URI"))
print("Connected to MongoDB Atlas!")
if os.environ["TEST_MODE"] in ("1", "True", "true"):
    db = client['_waifus']
else:
    db = client['waifus']
claims = db['claims']
print(f"Collection name: {db.name}.{claims.name}")
db = client['waifus']
waifus = db['core']
print(f"Collection name: {db.name}.{waifus.name}")

for record in claims.find():
    claim_id = uuid.UUID(bytes=record['_id'])
    
    if "name" in record:
        print(f"Skipping {claim_id}")
        continue
    
    waifu = waifus.find_one({"slug": record["slug"]})
    if waifu is None:
        print(f"Skipping {claim_id}, waifu not found for slug {record['slug']}")
        continue
    
    print(f"Updating {claim_id} with 'name': {waifu['name']}")
    claims.find_one_and_update(
        {"_id": record["_id"]},
        {"$set": {"name": waifu["name"]}}
    )
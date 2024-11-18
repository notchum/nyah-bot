import os
import uuid
from enum import Enum

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

print(f"Database URI: {os.getenv('DATABASE_URI')}")
client = MongoClient(os.getenv("DATABASE_URI"))
print("Connected to MongoDB Atlas!")
if os.getenv("TEST_MODE"):
    db = client['_waifus']
else:
    db = client['waifus']
claims = db['claims']
print(f"Collection name: {db.name}.{claims.name}")


result = claims.update_many(
    {},
    [
        {
            "$unset": [
                "price",
                "attack_mod",
                "defense_mod",
                "health_mod",
                "speed_mod",
                "magic_mod",
                "trait_common",
                "trait_uncommon",
                "trait_rare",
                "trait_legendary"
            ]
        },
        {
            "$set": {
                "trait": 0,
                "health_points": "$health"
            }
        }
    ]
)

print(result)

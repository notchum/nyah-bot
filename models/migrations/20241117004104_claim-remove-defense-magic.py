import os
import uuid
import random

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
                "defense",
                "magic",
            ]
        },
    ]
)

print(result)

for record in claims.find():
    claim_id = uuid.UUID(bytes=record['_id'])
    hp = random.choice(range(50, 251, 10)) # 50 - 250, step 10
    claims.find_one_and_update(
        {"_id": record["_id"]},
        {"$set": {
            "attack": random.choice(range(10, 101, 10)), # 10 - 100, step 10,
            "health": hp,
            "health_points": hp,
            "speed": random.choice(range(10, 101, 10)) # 10 - 100, step 10
        }}
    )
    
    print(f"Updated {claim_id}")

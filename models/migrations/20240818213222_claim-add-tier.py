import os
import uuid
from enum import Enum

from dotenv import load_dotenv
from pymongo import MongoClient

class Tiers(Enum):
    BRONZE  = 1
    SILVER  = 2
    GOLD    = 3
    EMERALD = 4
    RUBY    = 5
    DIAMOND = 6

TIER_PERCENTILE_MAP = {
    Tiers.DIAMOND: (99, 100),
    Tiers.RUBY: (95, 99),
    Tiers.EMERALD: (85, 95),
    Tiers.GOLD: (70, 85),
    Tiers.SILVER: (50, 70),
    Tiers.BRONZE: (0, 50),
}

def tier_from_rank(total_characters: int, popularity_rank: int) -> Tiers:
    percentile = (total_characters - popularity_rank + 1) / total_characters * 100

    for tier, (start_percentile, end_percentile) in TIER_PERCENTILE_MAP.items():
        if start_percentile < percentile <= end_percentile:
            return tier
    
    raise ValueError("No valid tier found for the given percentile.")

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

total_characters = waifus.estimated_document_count()

for record in claims.find():
    claim_id = uuid.UUID(bytes=record['_id'])
    
    if "tier" in record:
        print(f"Skipping {claim_id}")
        continue
    
    waifu = waifus.find_one({"slug": record["slug"]})
    if waifu is None:
        print(f"Defaulting {claim_id}, waifu not found for slug {record['slug']}")
        tier = Tiers.BRONZE
    elif waifu['popularity_rank'] is None:
        print(f"Defaulting {claim_id}, no rank found for waifu slug {record['slug']}")
        tier = Tiers.BRONZE
    elif waifu['popularity_rank'] > total_characters:
        print(f"Defaulting {claim_id}, rank is too high for {record['slug']}")
        tier = Tiers.BRONZE
    else:
        tier = tier_from_rank(total_characters, waifu['popularity_rank'])
        print(f"Updating {claim_id} with 'tier': {tier}")
    
    claims.find_one_and_update(
        {"_id": record["_id"]},
        {"$set": {"tier": tier.value}}
    )

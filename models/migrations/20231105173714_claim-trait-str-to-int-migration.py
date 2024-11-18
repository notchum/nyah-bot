import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

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

TRAITS = [
    [
        "Fire Affinity",
        "Water Affinity",
        "Wind Affinity",
        "Shadow Walker",
        "Silent Strike",
        "Ki Control",
        "Dragon Fist",
        "Iron Body",
        "Honor Bound",
        "Courageous Heart",
    ],
    [
        "Selective Element",
        "Pyromancer",
        "Teleportation",
        "Swordsmanship",
        "Archer's Precision",
        "Beast Form",
        "Spirit Form",
        "Rasengan",
        "Genjutsu Mastery",
    ],
    [
        "Elemental Combination",
        "Magic Affinity",
        "Blade Dancer",
        "Beast Tamer",
        "Illusionist",
        "Exclusive Code",
    ],
    [
        "Super Saiyan",
        "Death Note",
        "Divine Blessing",
        "Domain Expansion",
    ],
]

for trait_set, field in zip(TRAITS, ["trait_common", "trait_uncommon", "trait_rare", "trait_legendary"]):
    for i, trait in enumerate(trait_set):
        filter = {field: trait}
        update = {"$set": {field: i}}

        result = collection.update_many(filter, update)
        print(f"Number of documents matched: {result.matched_count}")
        print(f"Number of documents modified: {result.modified_count}")

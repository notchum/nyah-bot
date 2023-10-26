import os

import aiohttp_client_cache
from rethinkdb import r
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# Connect to RethinkDB
conn = r.connect(host=os.environ["RETHINKDB_SERVER_HOST"])

# Test guilds
TEST_GUILDS = [776929597567795247, 759514108625682473]

# Cog names
COGS = [filename[:-3] for filename in os.listdir("nyahbot/cogs") if filename.endswith(".py")]

# Assets folder
if not os.path.exists("assets"): os.mkdir("assets")
if not os.path.exists("assets/images"): os.mkdir("assets/images")

# Create aiohttp session
session = aiohttp_client_cache.CachedSession(
    cache=aiohttp_client_cache.CacheBackend(expire_after=600)
)
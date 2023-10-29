import os
import platform
import asyncio
import logging
import logging.handlers
from collections import namedtuple

import disnake
import aiohttp_client_cache
from disnake import Activity, ActivityType
from disnake.ext import commands
from rethinkdb import r
# from loguru import logger
from dotenv import load_dotenv

import nyahbot
from nyahbot.util.globals import *

Config = namedtuple(
    "Config",
    [
        "DEBUG",
        "DISCORD_BOT_TOKEN",
        "RETHINKDB_SERVER_HOST",
        "MAL_CLIENT_ID",
        "GOOGLE_KEY",
        "GOOGLE_SEARCH_ID",
        "PROXY_HTTP_URL",
        "WEBSCRAPE_URL",
    ],
)

class NyahBot(commands.InteractionBot):
    def __init__(self, *args, **kwargs):
        self.config = kwargs.pop("config", None)
        super().__init__(*args, **kwargs)

        # self.add_check(
        #     commands.bot_has_permissions(
        #         read_messages=True,
        #         send_messages=True,
        #         embed_links=True,
        #         attach_files=True,
        #         read_message_history=True,
        #         add_reactions=True,
        #         external_emojis=True,
        #     ).predicate
        # )

        # self.add_check(checks.general_check().predicate)

        self.activity = Activity(type=ActivityType.watching, name=f"v{nyahbot.__version__}")

        # Run the bot
        self.setup_logging()
        # await self.create_database_tables()
        # self.run(self.config.DISCORD_BOT_TOKEN)
    
    def setup_logging(self):
        self.logger = logging.getLogger("disnake")
        self.logger.setLevel(logging.DEBUG)

        # Create a rotating file handler
        handler = logging.handlers.TimedRotatingFileHandler(
            filename="log/nyah-bot.log",
            when="midnight",
            encoding="utf-8",
            backupCount=5,  # Rotate through 5 files
        )
        formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s")
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    async def create_database_tables(self):
        db_list = r.db_list().run(self.conn)
        self.logger.debug(f"Database list: {db_list}")
        # if "waifus" not in db_list:
        #     r.db_create("waifus").run(conn)
        #     r.db("waifus").table_create("claims").run(conn)
        #     r.db("waifus").table("claims").index_create("slug").run(conn)
        #     r.db("waifus").table("claims").index_create("user_id").run(conn)
        #     r.db("waifus").table("claims").index_create("guild_id").run(conn)
        #     r.db("waifus").table("claims").index_create("guild_user", [r.row["guild_id"], r.row["user_id"]]).run(conn)
        #     r.db("waifus").table_create("core", primary_key="slug").run(conn)
        #     r.db("waifus").table("core").index_create("name").run(conn)
        # if "nyah" not in db_list:
        #     r.db("nyah").table_create("guilds", primary_key="guild_id").run(conn)
        #     r.db("nyah").table_create("players").run(conn)
        #     r.db("nyah").table("players").index_create("guild_id").run(conn)
        #     r.db("nyah").table("players").index_create("guild_user", [r.row["guild_id"], r.row["user_id"]]).run(conn)
        # if "wars" not in db_list:
        #     r.db_create("wars").run(conn)
        #     r.db("wars").table_create("core").run(conn)
        #     r.db("wars").table_create("rounds").run(conn)
        #     r.db("wars").table_create("matches").run(conn)
        #     r.db("wars").table_create("battles").run(conn)
        #     r.db("wars").table_create("votes").run(conn)
    
    async def setup_hook(self):
        # self.logger.info(f"Init | shard_ids={self.shard_ids} | shard_count={self.shard_count}")
        
        for extension in [filename[:-3] for filename in os.listdir("nyahbot/cogs") if filename.endswith(".py")]:
            try:
                await self.load_extension(f"nyahbot.cogs.{extension}")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                self.logger.exception(f"Failed to load extension {extension}!\t{exception}")

        self.conn = r.connect(host=self.config.RETHINKDB_SERVER_HOST)
        self.session = aiohttp_client_cache.CachedSession(
            cache=aiohttp_client_cache.CacheBackend(expire_after=600)
        )

    async def on_ready(self):
        self.logger.info("------")
        self.logger.info(f"{self.user.name} v{nyahbot.__version__}")
        self.logger.info(f"ID: {self.user.id}")
        self.logger.info(f"Python version: {platform.python_version()}")
        self.logger.info(f"Disnake API version: {disnake.__version__}")
        self.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        self.logger.info("------")

    # async def on_shard_ready(self, shard_id: int):
    #     self.logger.info(f"Shard {shard_id} ready")

    async def close(self):
        await super().close()
        await self.session.close()

if __name__ == "__main__":
    # Load the environment variables
    load_dotenv()

    # Assets folder
    if not os.path.exists("assets"): os.mkdir("assets")
    if not os.path.exists("assets/images"): os.mkdir("assets/images")

    # Create config
    config = Config(
        DEBUG=os.getenv("DEBUG") in ("1", "True", "true"),
        DISCORD_BOT_TOKEN=os.environ["DISCORD_BOT_TOKEN"],
        RETHINKDB_SERVER_HOST=os.environ["RETHINKDB_SERVER_HOST"],
        MAL_CLIENT_ID=os.environ["MAL_CLIENT_ID"],
        GOOGLE_KEY=os.environ["GOOGLE_KEY"],
        GOOGLE_SEARCH_ID=os.environ["GOOGLE_SEARCH_ID"],
        PROXY_HTTP_URL=os.environ["PROXY_HTTP_URL"],
        WEBSCRAPE_URL=os.environ["WEBSCRAPE_URL"],
    )

    # Create intents
    intents = disnake.Intents.default()
    intents.members = True
    intents.message_content = True
    
    # Create bot
    bot = NyahBot(
        config=config,
        test_guilds=[776929597567795247, 759514108625682473],
        intents=intents,
    )
    bot.run(config.DISCORD_BOT_TOKEN)
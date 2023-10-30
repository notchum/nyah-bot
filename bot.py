import os
import logging
import platform
from collections import namedtuple

import aiohttp_client_cache
import disnake
from disnake import Activity, ActivityType
from disnake.ext import commands
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from helpers import Mongo
from models import (
    Waifu,
    Claim,
    NyahPlayer,
    NyahGuild,
    Vote,
    Battle,
    Match,
    Round,
    War,
)

VERSION = "0.2.3"

Config = namedtuple(
    "Config",
    [
        "DEBUG",
        "DISNAKE_LOGGING",
        "DISCORD_BOT_TOKEN",
        "DATABASE_URI",
        "MAL_CLIENT_ID",
        "GOOGLE_KEY",
        "GOOGLE_SEARCH_ID",
        "PROXY_HTTP_URL",
        "WEBSCRAPE_URL",
    ],
)

class NyahBot(commands.InteractionBot):
    def __init__(self, *args, **kwargs):
        self.config: Config = kwargs.pop("config", None)
        self.logger: logging.Logger = kwargs.pop("logger", None)
        super().__init__(*args, **kwargs)
        self.activity = Activity(type=ActivityType.watching, name=f"v{VERSION}")
    
    async def setup_hook(self):
        # Load cogs
        # for extension in [filename[:-3] for filename in os.listdir("nyahbot/cogs") if filename.endswith(".py")]:
        #     try:
        #         self.load_extension(f"nyahbot.cogs.{extension}")
        #     except Exception as e:
        #         exception = f"{type(e).__name__}: {e}"
        #         self.logger.exception(f"Failed to load extension {extension}!\t{exception}")
        self.load_extension("nyahbot.cogs.admin")

        # Initialize database
        self.client = AsyncIOMotorClient(self.config.DATABASE_URI, io_loop=self.loop)
        await init_beanie(self.client.nyah, document_models=[NyahGuild, NyahPlayer])
        await init_beanie(self.client.waifus, document_models=[Waifu, Claim])
        await init_beanie(self.client.wars, document_models=[War, Match, Battle, Round, Vote])
        self.mongo = Mongo()

        # Initialize aiohttp session
        self.session = aiohttp_client_cache.CachedSession(
            cache=aiohttp_client_cache.CacheBackend(expire_after=600)
        )

    async def on_ready(self):
        self.logger.info("------")
        self.logger.info(f"{self.user.name} v{VERSION}")
        self.logger.info(f"ID: {self.user.id}")
        self.logger.info(f"Python version: {platform.python_version()}")
        self.logger.info(f"Disnake API version: {disnake.__version__}")
        self.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        self.logger.info("------")

    async def close(self):
        await self.session.close()
        await super().close()

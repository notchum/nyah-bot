import os
import logging
import tempfile
import platform
from collections import namedtuple

import aiohttp_client_cache
import disnake
from disnake import Activity, ActivityType
from disnake.ext import commands
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from helpers import Mongo, API
from utils import WaifuState
from models import (
    Waifu,
    Claim,
    NyahConfig,
    NyahPlayer,
    NyahGuild,
    Vote,
    Battle,
    Match,
    Round,
    Event,
)

VERSION = "0.4.0"

Config = namedtuple(
    "Config",
    [
        "DEBUG",
        "DISNAKE_LOGGING",
        "TEST_MODE",
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
        for extension in [filename[:-3] for filename in os.listdir("cogs") if filename.endswith(".py")]:
            try:
                self.load_extension(f"cogs.{extension}")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                self.logger.exception(f"Failed to load extension {extension}!\t{exception}")

        # Initialize cache directory
        self.cache_dir = tempfile.mkdtemp()
        self.logger.debug(f"Initialized cache directory {self.cache_dir}")

        # Initialize database
        self.client = AsyncIOMotorClient(self.config.DATABASE_URI, io_loop=self.loop)
        if self.config.TEST_MODE:
            self.logger.warning("Running in test mode. Using test database.")
            await init_beanie(self.client.waifus, document_models=[Waifu])
            await init_beanie(self.client["_nyah"], document_models=[NyahConfig, NyahGuild, NyahPlayer])
            await init_beanie(self.client["_waifus"], document_models=[Claim])
            await init_beanie(self.client["_wars"], document_models=[Event, Match, Battle, Round, Vote])
        else:
            await init_beanie(self.client.nyah, document_models=[NyahConfig, NyahGuild, NyahPlayer])
            await init_beanie(self.client.waifus, document_models=[Waifu, Claim])
            await init_beanie(self.client.wars, document_models=[Event, Match, Battle, Round, Vote])
        self.mongo = Mongo()

        # Initialize aiohttp session
        self.session = aiohttp_client_cache.CachedSession(
            cache=aiohttp_client_cache.CacheBackend(expire_after=600)
        )
        self.api = API(self.session, self.cache_dir)

    async def on_ready(self):
        self.logger.info("------")
        self.logger.info(f"{self.user.name} v{VERSION}")
        self.logger.info(f"ID: {self.user.id}")
        self.logger.info(f"Python version: {platform.python_version()}")
        self.logger.info(f"Disnake API version: {disnake.__version__}")
        self.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        self.logger.info("------")

    async def close(self):
        self.clear_cache_dir()
        await self.session.close()
        await super().close()

    @property
    def waifus_cog(self) -> commands.Cog:
        return self.get_cog("Waifus")

    def clear_cache_dir(self):
        for file in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.logger.error(f"Error deleting {file}: {e}")
        os.rmdir(self.cache_dir)

    async def get_waifu_base_embed(self, waifu: Waifu) -> disnake.Embed:
        """ Get a bare-bones embed for a waifu.
            - Name
            - Husbando classification
            - Default Image
            - Series (with MAL links)

        """
        # Get links to series on MAL
        waifu_series = []
        for series in waifu.series:
            mal_url = await self.api.search_mal_series(series)
            if mal_url:
                waifu_series.append(f"[{series}]({mal_url})")
            else:
                waifu_series.append(series)
        waifu_series = "\n".join(waifu_series)
        
        embed = disnake.Embed(
            title=waifu.name + "  ♂️" if waifu.husbando else waifu.name + "  ♀️",
            url=waifu.url,
            color=disnake.Color.fuchsia()
        ) \
        .set_image(url=waifu.image_url) \
        .add_field(name="Appears In", value=waifu_series)

        return embed

    async def get_waifu_core_embed(self, waifu: Waifu) -> disnake.Embed:
        """ Get an ultra-detailed embed for a waifu.
            - Alternate names
            - Age & DOB
            - Measurements
            - Origin
            
        """
        embed = await self.get_waifu_base_embed(waifu)
        embed.description = (waifu.description[:4092] + "...") if len(waifu.description) > 4092 else waifu.description
        embed.color = disnake.Color.teal()
        embed.add_field(name="Original Name", value=waifu.original_name if waifu.original_name else "-") \
            .add_field(name="Romaji Name", value=waifu.romaji_name if waifu.romaji_name else "-") \
            .add_field(name="Place of Origin", value=waifu.origin if waifu.origin else "-") \
            .add_field(name="Age", value=waifu.age if waifu.age else "-") \
            .add_field(name="Date of Birth", value=waifu.date_of_birth if waifu.date_of_birth else "-") \
            .add_field(name="Height", value=waifu.height if waifu.height else "-") \
            .add_field(name="Weight", value=waifu.weight if waifu.weight else "-") \
            .add_field(name="Blood Type", value=waifu.blood_type if waifu.blood_type else "-") \
            .add_field(name="Bust", value=waifu.bust if waifu.bust else "-") \
            .add_field(name="Waist", value=waifu.waist if waifu.waist else "-") \
            .add_field(name="Hip", value=waifu.hip if waifu.hip else "-")
        return embed

    async def get_waifu_skills_embed(self, claim: Claim) -> disnake.Embed:
        waifu = await self.mongo.fetch_waifu(claim.slug)
        
        embed = await self.get_waifu_base_embed(waifu)
        embed.add_field(name="Price", value=claim.price_str)
        embed.add_field(name="Traits", value=claim.trait_str)
        embed.add_field(name=f"Skills ({claim.stats_str})", value=claim.skill_str)
        embed.set_footer(text=claim.id)
        embed.set_image(url=claim.image_url)
        return embed

    async def get_waifu_claim_embed(self, claim: Claim, owner: disnake.User | disnake.Member) -> disnake.Embed:
        """ Get an embed of a waifu just claimed.
            - Price listed.
            - Skills listed.
            - Traits listed.

            Parameters
            ----------
            waifu: `Waifu`
                The waifu to retrieve.
            owner: `disnake.User` | `disnake.Member`
                The owner of this waifu.
            
            Returns
            -------
            `disnake.Embed`
                The embed.
        """
        embed = await self.get_waifu_skills_embed(claim)
        embed.set_footer(text=f"{claim.id}")
        return embed

    async def get_waifu_harem_embed(self, claim: Claim) -> disnake.Embed:
        """ Get an embed of a waifu in a harem.
            - Embed color represents state.
            - Skills listed.
            - Price listed.
            - Traits listed.
            - Marriage status.
        
        """
        if claim.state == WaifuState.ACTIVE.value:
            color = disnake.Color.green()
            status = f"💕 Married"
        elif claim.state == WaifuState.COOLDOWN.value:
            color = disnake.Color.blue()
            status = f"❄️ Cooldown"
        elif claim.state == WaifuState.INACTIVE.value:
            color = disnake.Color.red()
            status = f"💔 Unmarried"
        
        embed = await self.get_waifu_skills_embed(claim)
        embed.add_field(name="Status", value=status)
        embed.color = color
        return embed

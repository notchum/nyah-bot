import os
import shutil
import tempfile
import platform
from collections import namedtuple

import aiohttp_client_cache
import disnake
from disnake import Activity, ActivityType
from disnake.ext import commands
from loguru import logger
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

import models
from helpers import Mongo, API
from helpers import utilities as utils
from util import WaifuState

VERSION = "0.9.0"

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
    ],
)


class NyahBot(commands.InteractionBot):
    def __init__(self, *args, **kwargs):
        self.config: Config = kwargs.pop("config", None)
        self.version = VERSION
        super().__init__(*args, **kwargs)
        self.before_slash_command_invoke(self.before_invoke)
        self.after_slash_command_invoke(self.after_invoke)
        self.activity = Activity(type=ActivityType.watching, name=f"v{VERSION}")
    
    async def setup_hook(self):
        # Initialize temporary directory
        self.create_temp_dir()
        logger.debug(f"Initialized temp directory {self.temp_dir}")

        # Load cogs
        for extension in utils.get_cog_names():
            try:
                self.load_extension(extension)
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                logger.exception(
                    f"Failed to load extension {extension}!\t{exception}"
                )

        # Initialize database
        self.client = AsyncIOMotorClient(self.config.DATABASE_URI, io_loop=self.loop)
        if self.config.TEST_MODE:
            await init_beanie(self.client["waifus"], document_models=[models.Waifu])
            await init_beanie(self.client["_nyah"], document_models=[models.NyahConfig, models.NyahGuild, models.NyahPlayer])
            await init_beanie(self.client["_waifus"], document_models=[models.Claim])
            await init_beanie(self.client["_wars"], document_models=[models.Event, models.Match, models.Battle, models.Round, models.Vote])
            logger.warning("Running in test mode. Connected to test database.")
        else:
            await init_beanie(self.client["nyah"], document_models=[models.NyahConfig, models.NyahGuild, models.NyahPlayer])
            await init_beanie(self.client["waifus"], document_models=[models.Waifu, models.Claim])
            await init_beanie(self.client["wars"], document_models=[models.Event, models.Match, models.Battle, models.Round, models.Vote])
            logger.success("Connected to database.")

        # Create the global bot settings entry if it doesn't exist
        await self.create_settings_entry()
        
        # Initialize aiohttp session
        self.session = aiohttp_client_cache.CachedSession(
            cache=aiohttp_client_cache.CacheBackend(expire_after=600),
            loop=self.loop
        )

        # Set up interfaces
        self.api = API(self.session, self.cache_dir)
        self.mongo = Mongo()

    async def on_ready(self):
        # fmt: off
        logger.info("------")
        logger.info(f"{self.user.name} v{self.version}")
        logger.info(f"ID: {self.user.id}")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Disnake API version: {disnake.__version__}")
        logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        logger.info("------")
        # fmt: on

    async def close(self):
        await self.session.close()
        await super().close()

    def create_temp_dir(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), "tmp-nyah-bot")
        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)

    def clear_temp_dir(self):
        for file in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Error deleting {file}: {e}")

    async def create_settings_entry(self):
        return #TODO remove when settings is renamed
        settings_doc = await models.BotSettings.find_all().to_list()
        if len(settings_doc) == 0:
            settings_doc = await models.BotSettings.insert_one(
                models.BotSettings(toggle=False)
            )
            logger.success(f"Created settings entry for nyah-bot [{settings_doc.id}]")

    @property
    def waifus_cog(self) -> commands.Cog:
        return self.get_cog("Waifus")

    async def before_invoke(self, inter: disnake.ApplicationCommandInteraction):
        nyah_player = await models.NyahPlayer.find_one(
            models.NyahPlayer.user_id == inter.author.id
        )
        
        channel_id = nyah_player.last_command_channel_id
        message_id = nyah_player.last_command_message_id
        if not channel_id or not message_id:
            return
        
        # grab the channel
        # p_channel = self.get_partial_messageable(channel_id, type=disnake.TextChannel)
        channel = self.get_channel(channel_id)
        if not channel:
            channel = await self.fetch_channel(channel_id)
        
        # attempt to grab the message partial
        p_message = channel.get_partial_message(message_id)
        if p_message:
            return await p_message.edit(view=None)
        
        # if that fails, fetch the message
        message = await channel.fetch_message(message_id)
        if message:
            return await message.edit(view=None)

    async def after_invoke(self, inter: disnake.ApplicationCommandInteraction):
        nyah_player = await models.NyahPlayer.find_one(
            models.NyahPlayer.user_id == inter.author.id
        )
        
        message = await inter.original_response()
        if not message.components or message.flags.ephemeral:
            nyah_player.last_command_name = None
            nyah_player.last_command_channel_id = None
            nyah_player.last_command_message_id = None
        else:
            nyah_player.last_command_name = inter.data.name
            nyah_player.last_command_channel_id = inter.channel.id
            nyah_player.last_command_message_id = message.id
        
        await nyah_player.save()

    async def get_waifu_base_embed(self, waifu: models.Waifu) -> disnake.Embed:
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

    async def get_waifu_core_embed(self, waifu: models.Waifu) -> disnake.Embed:
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

    async def get_waifu_skills_embed(self, claim: models.Claim) -> disnake.Embed:
        waifu = await self.mongo.fetch_waifu(claim.slug)
        
        embed = await self.get_waifu_base_embed(waifu)
        embed.add_field(name="Price", value=claim.price_str)
        embed.add_field(name="Traits", value=claim.trait_str)
        embed.add_field(name=f"Skills ({claim.stats_str})", value=claim.skill_str)
        embed.set_footer(text=claim.id)
        embed.set_image(url=claim.image_url)
        return embed

    async def get_waifu_claim_embed(self, claim: models.Claim, owner: disnake.User | disnake.Member) -> disnake.Embed:
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

    async def get_waifu_harem_embed(self, claim: models.Claim) -> disnake.Embed:
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

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
import utils
from helpers import Mongo, API

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
        self.api = API(self.session, self.temp_dir)
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

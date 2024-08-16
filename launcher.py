import os
import asyncio

import disnake
from loguru import logger
from dotenv import load_dotenv

from bot import NyahBot, Config


async def main():
    # Load the environment variables
    load_dotenv()

    # Create config
    config = Config(
        DEBUG=os.environ["DEBUG"] in ("1", "True", "true"),
        DISNAKE_LOGGING=os.environ["DISNAKE_LOGGING"] in ("1", "True", "true"),
        TEST_MODE=os.environ["TEST_MODE"] in ("1", "True", "true"),
        DISCORD_BOT_TOKEN=os.environ["DISCORD_BOT_TOKEN"],
        DATABASE_URI=os.environ["DATABASE_URI"],
        MAL_CLIENT_ID=os.environ["MAL_CLIENT_ID"],
        GOOGLE_KEY=os.environ["GOOGLE_KEY"],
        GOOGLE_SEARCH_ID=os.environ["GOOGLE_SEARCH_ID"],
        PROXY_HTTP_URL=os.environ["PROXY_HTTP_URL"],
    )

    # Create logger
    logger.add(
        "logs/nyah-bot.log", level="DEBUG" if config.DEBUG else "INFO", rotation="12:00"
    )
    if config.DISNAKE_LOGGING:
        pass  # TODO logger = logging.getLogger("disnake")

    # Create intents
    intents = disnake.Intents.default()
    intents.members = True
    intents.message_content = True
    
    # Create bot
    bot = NyahBot(
        config=config,
        test_guilds=[776929597567795247, 759514108625682473, 1169450511133589604],
        intents=intents,
    )
    await bot.setup_hook()
    await bot.start(config.DISCORD_BOT_TOKEN)


asyncio.run(main())

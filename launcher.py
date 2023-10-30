import os
import asyncio
import logging
import logging.handlers

import disnake
from dotenv import load_dotenv

from bot import NyahBot, Config

async def main():
    # Load the environment variables
    load_dotenv()

    # Assets folder
    if not os.path.exists("assets"): os.mkdir("assets")
    if not os.path.exists("assets/images"): os.mkdir("assets/images")

    # Create config
    config = Config(
        DEBUG=os.environ["DEBUG"] in ("1", "True", "true"),
        DISNAKE_LOGGING=os.environ["DISNAKE_LOGGING"] in ("1", "True", "true"),
        DISCORD_BOT_TOKEN=os.environ["DISCORD_BOT_TOKEN"],
        DATABASE_URI=os.environ["DATABASE_URI"],
        MAL_CLIENT_ID=os.environ["MAL_CLIENT_ID"],
        GOOGLE_KEY=os.environ["GOOGLE_KEY"],
        GOOGLE_SEARCH_ID=os.environ["GOOGLE_SEARCH_ID"],
        PROXY_HTTP_URL=os.environ["PROXY_HTTP_URL"],
        WEBSCRAPE_URL=os.environ["WEBSCRAPE_URL"],
    )

    # Create logger
    if config.DISNAKE_LOGGING:
        logger = logging.getLogger("disnake")
    else:
        logger = logging.getLogger("nyahbot")
    logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)

    handler = logging.handlers.TimedRotatingFileHandler(
        filename="log/nyah-bot.log",
        when="midnight",
        encoding="utf-8",
        backupCount=5,  # Rotate through 5 files
    )
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create intents
    intents = disnake.Intents.default()
    intents.members = True
    intents.message_content = True
    
    # Create bot
    bot = NyahBot(
        config=config,
        logger=logger,
        test_guilds=[776929597567795247, 759514108625682473],
        intents=intents,
    )
    await bot.setup_hook()
    await bot.start(config.DISCORD_BOT_TOKEN)

asyncio.run(main())
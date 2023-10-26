import os
import platform

import disnake
from disnake import Activity, ActivityType
from disnake.ext import commands, tasks
from rethinkdb import r
from loguru import logger

import nyahbot
from nyahbot.util.globals import *

intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.InteractionBot(
    test_guilds=TEST_GUILDS,
    intents=intents
)

##*************************************************##
##********              EVENTS              *******##
##*************************************************##

@bot.event
async def on_ready():
    """ Client event when it boots up. """
    logger.info("------")
    logger.info(f"{bot.user.name} v{nyahbot.__version__}")
    logger.info(f"ID: {bot.user.id}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Disnake API version: {disnake.__version__}")
    logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    logger.info("------")
    status_task.start()

    # Create databases and tables
    db_list = r.db_list().run(conn)
    if "waifus" not in db_list:
        r.db_create("waifus").run(conn)
        r.db("waifus").table_create("claims").run(conn)
        r.db("waifus").table("claims").index_create("slug").run(conn)
        r.db("waifus").table("claims").index_create("user_id").run(conn)
        r.db("waifus").table("claims").index_create("guild_id").run(conn)
        r.db("waifus").table("claims").index_create("guild_user", [r.row["guild_id"], r.row["user_id"]]).run(conn)
        r.db("waifus").table_create("core", primary_key="slug").run(conn)
        r.db("waifus").table("core").index_create("name").run(conn)
    if "nyah" not in db_list:
        r.db("nyah").table_create("guilds", primary_key="guild_id").run(conn)
        r.db("nyah").table_create("players").run(conn)
        r.db("nyah").table("players").index_create("guild_id").run(conn)
        r.db("nyah").table("players").index_create("guild_user", [r.row["guild_id"], r.row["user_id"]]).run(conn)
    if "wars" not in db_list:
        r.db_create("wars").run(conn)
        r.db("wars").table_create("core").run(conn)
        r.db("wars").table_create("rounds").run(conn)
        r.db("wars").table_create("matches").run(conn)
        r.db("wars").table_create("battles").run(conn)
        r.db("wars").table_create("votes").run(conn)

##*************************************************##
##********              TASKS               *******##
##*************************************************##

@tasks.loop(seconds=1.0, count=1)
async def status_task():
    await bot.change_presence(activity=Activity(type=ActivityType.watching, name=f"v{nyahbot.__version__}"))

##*************************************************##
##********          START THE BOT           *******##
##*************************************************##

if __name__ == "__main__":
    # Create logging file
    logger.add("log/nyah-bot.log", rotation="12:00")

    # Load the cogs into the bot
    for extension in COGS:
        try:
            bot.load_extension(f"nyahbot.cogs.{extension}")
        except Exception as e:
            exception = f"{type(e).__name__}: {e}"
            logger.exception(f"Failed to load extension {extension}!\t{exception}")

    # Runs the bot (brings it to life)
    bot.run(os.environ["DISCORD_BOT_TOKEN"])
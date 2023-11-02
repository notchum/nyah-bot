import os
import datetime
import tempfile

import disnake
from disnake.ext import commands, tasks

from bot import NyahBot

class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot
        self.clean_cache_dir.start()

    ##*************************************************##
    ##********           ABSTRACTIONS           *******##
    ##*************************************************##

    ##*************************************************##
    ##********              EVENTS              *******##
    ##*************************************************##

    ##*************************************************##
    ##********              TASKS               *******##
    ##*************************************************##

    @tasks.loop(hours=1)
    async def clean_cache_dir(self):
        """ Clean the cache directory periodically. """
        self.bot.logger.debug(f"Cleaning cache directory... [loop #{self.clean_cache_dir.current_loop}]")

        if not os.path.exists(self.bot.cache_dir):
            self.bot.logger.debug("Cache directory does not exist. Recreating...")
            self.bot.cache_dir = tempfile.mkdtemp()
            self.bot.logger.debug(f"Reinitialized cache directory {self.bot.cache_dir}")

        for file in os.listdir(self.bot.cache_dir):
            # Only delete files that are older than 1 hour
            file_path = os.path.join(self.bot.cache_dir, file)
            if os.path.getmtime(file_path) < (datetime.datetime.now() - datetime.timedelta(hours=1)).timestamp():
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.bot.logger.info(f"Deleted {file}")
                except Exception as e:
                    self.bot.logger.error(f"Error deleting {file}: {e}")

    @clean_cache_dir.before_loop
    async def init_clean_cache_dir(self):
        await self.bot.wait_until_ready()

    ##*************************************************##
    ##********             COMMANDS             *******##
    ##*************************************************##

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(Tasks(bot))
import os
import datetime
import tempfile

from disnake.ext import commands, tasks
from loguru import logger

from bot import NyahBot

class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot
        self.clean_temp_dir.start()

    @tasks.loop(hours=1.0)
    async def clean_temp_dir(self):
        """Clears all files from the bot's temporary directory."""
        logger.debug(
            f"Cleaning temp directory... [loop #{self.clean_temp_dir.current_loop}]"
        )

        # The first iteration of this task is executed when
        # the bot starts. This checks if we are in that
        # initial loop
        if self.clean_temp_dir.current_loop == 0:
            # If there is anything that needs to
            # happen on the first iteration of a
            # task, then put it here.
            pass

        # Delete all files from the temporary directory
        self.bot.clear_temp_dir()
        logger.info("Finished clearing temp directory.")

    @clean_temp_dir.before_loop
    async def wait_before_tasks(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(Tasks(bot))

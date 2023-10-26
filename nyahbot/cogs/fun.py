import os

import disnake
from disnake.ext import commands

from nyahbot.util import utilities

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ##*************************************************##
    ##********           ABSTRACTIONS           *******##
    ##*************************************************##

    ##*************************************************##
    ##********              EVENTS              *******##
    ##*************************************************##

    ##*************************************************##
    ##********              TASKS               *******##
    ##*************************************************##

    ##*************************************************##
    ##********             COMMANDS             *******##
    ##*************************************************##

    @commands.slash_command()
    async def ddlc(
        self,
        inter: disnake.ApplicationCommandInteraction,
        character: str,
        text: str
    ):
        """ Create a Doki Doki meme. https://edave64.github.io/Doki-Doki-Dialog-Generator/release/

            Parameters
            ----------
            character: `str`
                A DDLC character's name.
            text: `str`
                Meme text.
        """
        return await inter.response.send_message(
            embed=utilities.get_error_embed("Not implemented :("),
            ephemeral=True
        )

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    # required_env_vars = ['IMGFLIP_USERNAME', 'IMGFLIP_PASSWORD']
    # for env_var in required_env_vars:
    #     if env_var not in os.environ or not os.environ[env_var]:
    #         return logger.error(f"Cannot load cog 'TextGen' | {env_var} not in environment!")
    bot.add_cog(Fun(bot))
import os

import disnake
from disnake.ext import commands

from bot import NyahBot
from helpers import SuccessEmbed, ErrorEmbed

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot

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
            embed=ErrorEmbed("Not implemented :("),
            ephemeral=True
        )

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
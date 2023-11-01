import os

import disnake
from disnake.ext import commands

from helpers import SuccessEmbed, ErrorEmbed

class Shop(commands.Cog):
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
    async def shop(self, inter: disnake.ApplicationCommandInteraction):
        """ View the shop! """
        return await inter.response.send_message(
            embed=ErrorEmbed("Not implemented :("),
            ephemeral=True
        )

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(Shop(bot))
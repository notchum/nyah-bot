import asyncio

import disnake
from disnake.ext import commands

from bot import NyahBot
from helpers import SuccessEmbed, ErrorEmbed
from utils import Emojis
from views.gambling import SlotMachine, SlotsView

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
    
    @commands.slash_command()
    async def slots(
        self,
        inter: disnake.ApplicationCommandInteraction,
        bet: int = commands.Param(gt=0)
    ):
        """ Play a game of slots. """
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)

        if bet > nyah_player.money:
            return await inter.response.send_message(
                embed=ErrorEmbed("You don't have enough nyahcoins!"),
                ephemeral=True
            )
        
        await inter.response.defer()

        machine = SlotMachine()

        slots_view = SlotsView(machine, inter.author)
        message = await inter.edit_original_response(embed=machine.embeds[0], view=slots_view)
        slots_view.message = message

        await slots_view.wait()
        
        await nyah_player.add_user_money(-bet)

        for embed in machine.embeds:
            await inter.edit_original_response(embed=embed)
            await asyncio.sleep(0.5)
        
        payout = machine.calculate_payout(bet)
        if payout > 0:
            await nyah_player.add_user_money(payout)
            
            result_embed = disnake.Embed(
                title="You won!",
                description=f"You won `{payout:,}` {Emojis.COINS}!",
                color=disnake.Color.green()
            )
        else:
            result_embed = disnake.Embed(
                title="You lost!",
                description=f"You lost `{bet:,}` {Emojis.COINS}!",
                color=disnake.Color.red()
            )

        await inter.edit_original_response(embeds=[machine.embeds[-1], result_embed])

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
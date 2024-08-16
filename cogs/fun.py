import disnake
from disnake.ext import commands

from bot import NyahBot
from helpers import ErrorEmbed
from util import Emojis
from views.gambling import SlotMachine, SlotsView

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot

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
        #TODO
        return await inter.response.send_message(
            embed=ErrorEmbed("Not implemented :("),
            ephemeral=True
        )
    
    @commands.slash_command()
    async def slots(self, inter: disnake.ApplicationCommandInteraction):
        """ Play a game of slots. """
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)
        machine = SlotMachine(nyah_player)

        if nyah_player.money < machine.bet:
            return await inter.response.send_message(
                embed=ErrorEmbed(f"You don't have enough money to play slots! You need at least `{machine.min_bet:,}` {Emojis.COINS}"),
                ephemeral=True
            )
        
        await inter.response.defer()

        slots_view = SlotsView(machine, inter.author)
        message = await inter.edit_original_response(embed=machine.current_embed, view=slots_view)
        slots_view.message = message


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))

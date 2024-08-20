import asyncio
from datetime import timedelta

import disnake
from disnake.ext import commands

from bot import NyahBot
from helpers import ErrorEmbed, WaifuBaseEmbed
from utils.constants import Emojis, Tiers, Fusions, TIER_TITLE_MAP, FUSION_TIER_MAP
from views import FusionStageOneView, FusionStageTwoView
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
        waifus = await self.bot.mongo.fetch_random_waifus(2)
        poll = disnake.Poll(
            question=f"{Emojis.RED_BOX} {waifus[0].name} vs. {waifus[1].name} {Emojis.BLUE_BOX}",
            answers=[
                disnake.PollAnswer(
                    disnake.PollMedia(
                        text=waifus[0].name,
                        emoji=Emojis.RED_BOX
                    )
                ),
                disnake.PollAnswer(
                    disnake.PollMedia(
                        text=waifus[1].name,
                        emoji=Emojis.BLUE_BOX
                    )
                ),
            ],
            duration=timedelta(hours=1),
        )
        await inter.response.send_message(
            embed=disnake.Embed(

            ) \
                .set_image(url="https://cdn.discordapp.com/attachments/1169450512500936736/1274465476487024732/vs.jpg?ex=66c259f8&is=66c10878&hm=5a940ef7fce7b376e30db60d218f4badce24cc8a8847284a122d2b2455303324&") \
                .set_footer(text="Poll ends in 30 seconds | Ignore the duration on the poll"),
            poll=poll
        )

        await asyncio.sleep(30)

        message = await inter.original_response()
        message = await inter.channel.fetch_message(message.id)
        if message and message.poll:
            print(message.poll.answers[0].count)
            print(message.poll.answers[1].count)
            await message.poll.expire()


    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if (message.author.id == self.bot.user.id
            and message.embeds
            and message.embeds[0].type == 'poll_result'):
            print()
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
        print()

    
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

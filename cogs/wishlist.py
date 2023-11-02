import re
from collections import deque

import disnake
from disnake.ext import commands

from bot import NyahBot
from views import WaifuWishlistView
from helpers import SuccessEmbed, ErrorEmbed
from utils import Emojis, Money

class Wishlist(commands.Cog):
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
    async def wishlist(self, inter: disnake.ApplicationCommandInteraction):
        """ Top-level command group for wishlisting waifus. """
        pass
    
    @wishlist.sub_command()
    async def add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        waifu: str
    ):
        """ Wishlist a waifu!
        
            Parameters
            ----------
            waifu: `str`
                The waifu to wishlist.
        """
        await inter.response.defer()

        if re.search(r"\[.*\]", waifu):
            match = re.match(r"^(.*?)\s*\[(.*?)\]$", waifu)
            name = match.group(1).strip()
            series = match.group(2).strip()

            result = await self.bot.mongo.fetch_waifu_by_name_series(name, series)
        else:
            result = await self.bot.mongo.fetch_waifu_by_name(waifu)
        waifu = result[0]

        if not result:
            return await inter.edit_original_response(
                embed=ErrorEmbed(f"Couldn't find `{name}` in the waifu database!")
            )
        
        embed = await self.bot.get_waifu_base_embed(waifu)
        embed.description = f"Wishlist __**{waifu.name}**__ for `{Money.WISHLIST_COST.value:,}` {Emojis.COINS}?"
        
        wishlist_view = WaifuWishlistView(
            embed=embed,
            waifu=waifu,
            author=inter.author
        )
        return await inter.edit_original_response(embed=embed, view=wishlist_view)

    @wishlist.sub_command()
    async def show(self, inter: disnake.ApplicationCommandInteraction):
        """ Show your wishlist. """
        await inter.response.defer()
        
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)
        if not nyah_player.wishlist:
            return await inter.edit_original_response(
                embed=ErrorEmbed(f"{inter.author.mention} your wishlist is empty!\n\n"
                                      f"Use `/wishlist add` to add a waifu to your wishlist to increase odds of getting it with `/getmywaifu`")
            )
        
        drop_chance_field = ""
        waifu_name_field = ""
        for i, slug in enumerate(set(nyah_player.wishlist), 1):
            drop_chance = int(0.05 * nyah_player.wishlist.count(slug) * 100)
            waifu = await self.bot.mongo.fetch_waifu(slug)
            waifu_name_field += f"`{i}` {waifu.name}\n"
            drop_chance_field += f"`{drop_chance: >3}%`\n"

        embed = disnake.Embed(
            color=disnake.Color.dark_purple()
        ) \
        .set_author(name=f"{inter.author.name}'s Wishlist 🌠", icon_url=inter.author.display_avatar.url) \
        .add_field(name="Name", value=waifu_name_field) \
        .add_field(name="Drop Chance", value=drop_chance_field)

        return await inter.edit_original_response(embed=embed)

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

    @add.autocomplete("waifu")
    async def waifu_name_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        if not user_input:
            user_input = "a"
        waifus = await self.bot.mongo.fetch_waifu_by_name(user_input)
        return deque([f"{waifu.name} [{waifu.series[0]}]" for waifu in waifus if len(waifu.series)], maxlen=25)

def setup(bot: commands.Bot):
    bot.add_cog(Wishlist(bot))
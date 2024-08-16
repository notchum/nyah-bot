import disnake
from loguru import logger

import models
from helpers import Mongo
from util import Emojis, Money

mongo = Mongo()

class WaifuWishlistView(disnake.ui.View):
    def __init__(self, embed: disnake.Embed, waifu: models.Waifu, author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.embed = embed
        self.waifu = waifu
        self.author = author

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(label="Wishlist", emoji="🌠", style=disnake.ButtonStyle.green)
    async def wishlist(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        nyah_player = await mongo.fetch_nyah_player(inter.author)
        
        if nyah_player.money < Money.WISHLIST_COST.value:
            price_diff = Money.WISHLIST_COST.value - nyah_player.money
            confirmation_embed = disnake.Embed(
                description=f"{inter.author.mention}\nYou need `{price_diff:,}` {Emojis.COINS}",
                color=disnake.Color.red()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Failed to wishlist '{self.waifu.slug}'")
        elif int(0.05 * nyah_player.wishlist.count(self.waifu.slug) * 100) == 100:
            confirmation_embed = disnake.Embed(
                description=f"{inter.author.mention}\nYou have already wishlisted **__{self.waifu.name}__** the maximum number of times!",
                color=disnake.Color.red()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Failed to wishlist '{self.waifu.slug}'")
        else:
            await nyah_player.add_user_money(-Money.WISHLIST_COST.value)
            nyah_player.wishlist.append(self.waifu.slug)
            num_wishlists = nyah_player.wishlist.count(self.waifu.slug)
            await mongo.update_nyah_player(nyah_player)
        
            confirmation_embed = disnake.Embed(
                description=f"{inter.author.mention}\n__**{self.waifu.name}**__ has been wishlisted for `{Money.WISHLIST_COST.value:,}` {Emojis.COINS}.\n"
                            f"You have wishlisted this waifu `{num_wishlists}` times",
                color=disnake.Color.fuchsia()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Wishlisted '{self.waifu.slug}'")

        await inter.response.edit_message(embeds=[self.embed, confirmation_embed], view=None)
    
    @disnake.ui.button(label="Cancel", emoji="✖️", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        cancel_embed = disnake.Embed(
            description=f"Wishlisting cancelled.\n",
            color=disnake.Color.red()
        )
        
        await inter.response.edit_message(embeds=[self.embed, cancel_embed], view=None)
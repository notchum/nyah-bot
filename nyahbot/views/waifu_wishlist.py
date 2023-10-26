import disnake
from loguru import logger

from nyahbot.util.dataclasses import Waifu
from nyahbot.util.constants import Money, Emojis
from nyahbot.util import reql_helpers

class WaifuWishlistView(disnake.ui.View):
    def __init__(self, embed: disnake.Embed, waifu: Waifu, author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.embed = embed
        self.waifu = waifu
        self.author = author

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(label="Wishlist", emoji="🌠", style=disnake.ButtonStyle.green)
    async def wishlist(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        war_user = await reql_helpers.get_nyah_user(inter.author)
        
        if war_user.money < Money.WISHLIST_COST.value:
            price_diff = Money.WISHLIST_COST.value - war_user.money
            confirmation_embed = disnake.Embed(
                description=f"{inter.author.mention}\nYou need `{price_diff:,}` {Emojis.COINS}",
                color=disnake.Color.fuchsia()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Failed to wishlist '{self.waifu.slug}'")
        else:
            war_user.money -= Money.WISHLIST_COST.value
            war_user.wishlist.append(self.waifu.slug)
            num_wishlists = war_user.wishlist.count(self.waifu.slug)
            await reql_helpers.set_nyah_user(war_user)
        
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
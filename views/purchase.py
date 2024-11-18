import disnake
from loguru import logger

import models
from helpers import Mongo, WaifuClaimEmbed
from utils.constants import Emojis
from views import WaifuClaimView

mongo = Mongo()

class WaifuPurchaseView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, embed: disnake.Embed, waifu: models.Waifu, author: disnake.User | disnake.Member, cost: int) -> None:
        super().__init__()
        self.embed = embed
        self.waifu = waifu
        self.author = author
        self.cost = cost

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(label="Buy", emoji=Emojis.SHOPPING_CART, style=disnake.ButtonStyle.green)
    async def buy(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        nyah_player = await mongo.fetch_nyah_player(inter.author)
        
        if nyah_player.money < self.cost:
            price_diff = self.cost - nyah_player.money
            confirmation_embed = disnake.Embed(
                description=f"{inter.author.mention}\nYou need `{price_diff:,}` {Emojis.TICKET}",
                color=disnake.Color.red()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Failed to buy '{self.waifu.slug}'")
        else:
            await nyah_player.add_user_money(-self.cost)

            # Generate claim
            claim = await nyah_player.generate_claim(self.waifu)

            # Send the waifu
            waifu_embed = WaifuClaimEmbed(self.waifu, claim)
            claim_view = WaifuClaimView(claim, inter.author)
            message = await self.message.reply(
                content=f"**A {'husbando' if self.waifu.husbando else 'waifu'} for {inter.author.mention} :3**",
                embed=waifu_embed,
                view=claim_view
            )
            claim_view.message = message

            # Insert claim in db
            claim.guild_id=message.guild.id
            claim.channel_id=message.channel.id
            claim.message_id=message.id
            claim.jump_url=message.jump_url
            claim.timestamp=message.created_at
            await mongo.insert_claim(claim)

            # Update harem in db
            harem = await mongo.fetch_harem(inter.author)
            await harem.reindex()
        
            confirmation_embed = disnake.Embed(
                description=f"{inter.author.mention}\n__**{self.waifu.name}**__ has been bought for `{self.cost:,}` {Emojis.TICKET}.\n",
                color=disnake.Color.fuchsia()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Bought '{self.waifu.slug}'")

        await inter.response.edit_message(embeds=[self.embed, confirmation_embed], view=None)
    
    @disnake.ui.button(label="Cancel", emoji=Emojis.CROSS_MARK, style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        cancel_embed = disnake.Embed(
            description=f"Purchase cancelled.\n",
            color=disnake.Color.red()
        )
        
        await inter.response.edit_message(embeds=[self.embed, cancel_embed], view=None)
import disnake
from loguru import logger

from nyahbot.util.dataclasses import Claim
from nyahbot.util.constants import (
    Emojis,
    WaifuState,
)
from nyahbot.util import (
    helpers,
    reql_helpers,
)

class WaifuClaimView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, claim: Claim, author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.claim = claim
        self.original_author = author

        # self.add_item(
        #     item=disnake.ui.Button(
        #         label="View Waifu",
        #         style=disnake.ButtonStyle.link,
        #         url=f"https://mywaifulist.moe/waifu/{self.claim.slug}"
        #     )
        # )

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

    @disnake.ui.button(label="Sell", emoji=Emojis.COINS)
    async def sell(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await helpers.sell_waifu(inter.author, self.claim)
        
        waifu = await reql_helpers.get_waifu_core(self.claim.slug)
        sold_embed = disnake.Embed(
            description=f"Sold **__{waifu.name}__** for {self.claim.price_str()}",
            color=disnake.Color.gold()
        )
        await inter.response.edit_message(embeds=[self.message.embeds[0], sold_embed], view=None)

        logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                    f"{inter.channel.name}[{inter.channel.id}] | "
                    f"{inter.author}[{inter.author.id}] | "
                    f"Sold {self.claim.slug}[{self.claim.id}]")
    
    @disnake.ui.button(label="Marry", emoji="💕")
    async def marry(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        nyah_guild = await reql_helpers.get_nyah_guild(inter.guild)
        num_marriages = await reql_helpers.get_harem_married_size(inter.guild, inter.author)

        if num_marriages >= nyah_guild.waifu_max_marriages:
            result_embed = disnake.Embed(
                description=f"You are already at the maximum amount of marriages!",
                color=disnake.Color.red()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Failed to marry {self.claim.slug}[{self.claim.id}]")
        else:
            self.claim.state = WaifuState.ACTIVE.name
            await reql_helpers.set_waifu_claim(self.claim)
            await helpers.reindex_guild_user_harem(inter.guild, inter.author)

            waifu = await reql_helpers.get_waifu_core(self.claim.slug)
            result_embed = disnake.Embed(
                description=f"Married **__{waifu.name}__** 💕",
                color=disnake.Color.green()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Married {self.claim.slug}[{self.claim.id}]")
        
        await inter.response.edit_message(embeds=[self.message.embeds[0], result_embed], view=None)
import disnake
from loguru import logger

import models
from helpers import Mongo
from utils.constants import Emojis, Money

mongo = Mongo()

class WaifuSkillView(disnake.ui.View):
    message: disnake.Message
    
    def __init__(self, claim: models.Claim, author: disnake.User | disnake.Member) -> None:
        super().__init__(timeout=30.0)
        self.claim = claim
        self.author = author
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id
    
    async def on_timeout(self) -> None:
        await self.message.edit(view=None)
    
    @disnake.ui.button(label="Reroll Skills", emoji="🎲", style=disnake.ButtonStyle.green)
    async def reroll(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        nyah_player = await mongo.fetch_nyah_player(inter.author)
        
        if nyah_player.money < Money.SKILL_COST.value:
            price_diff = Money.SKILL_COST.value - nyah_player.money
            confirmation_embed = disnake.Embed(
                description=f"{inter.author.mention}\nYou need `{price_diff:,}` {Emojis.COINS}",
                color=disnake.Color.fuchsia()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Failed to reroll skills {self.claim.slug}[{self.claim.id}]")
            
            self.children = []
        else:
            await nyah_player.add_user_money(-Money.SKILL_COST.value)

            await self.claim.roll_skills()
            await self.claim.apply_trait_modifiers()
            await mongo.update_claim(self.claim)

            waifu = await mongo.fetch_waifu(self.claim.slug)

            confirmation_embed = disnake.Embed(
                description=f"Successfully rerolled skills for **__{waifu.name}__**!\n"
                            f"Your balance is now `{nyah_player.money:,}` {Emojis.COINS}",
                color=disnake.Color.green()
            )
            confirmation_embed.add_field(name=f"New Skills ({self.claim.stats_str})", value=self.claim.skill_str)

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Rerolled skills {self.claim.slug}[{self.claim.id}]")

        self.reroll.label = "Reroll Skills Again?"
        await inter.response.edit_message(embeds=[self.message.embeds[0], confirmation_embed], view=self)

    @disnake.ui.button(label="Cancel", emoji=Emojis.CROSS_MARK, style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.edit_message(view=None)
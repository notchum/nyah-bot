import random

import disnake
from loguru import logger

from nyahbot.util.constants import Money, Emojis
from nyahbot.util.dataclasses import Claim
from nyahbot.util import reql_helpers

class WaifuSkillView(disnake.ui.View):
    message: disnake.Message
    
    def __init__(self, claim: Claim, author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.claim = claim
        self.author = author
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id
    
    async def on_timeout(self) -> None:
        await self.message.edit(view=None)
    
    @disnake.ui.button(label="Reroll Skills", emoji="🎲", style=disnake.ButtonStyle.green)
    async def reroll(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        war_user = await reql_helpers.get_nyah_user(inter.author)
        
        if war_user.money < Money.SKILL_COST.value:
            price_diff = Money.SKILL_COST.value - war_user.money
            confirmation_embed = disnake.Embed(
                description=f"{inter.author.mention}\nYou need `{price_diff:,}` {Emojis.COINS}",
                color=disnake.Color.fuchsia()
            )

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Failed to reroll skills {self.claim.slug}[{self.claim.id}]")
        else:
            war_user.money -= Money.SKILL_COST.value
            await reql_helpers.set_nyah_user(war_user)

            # TODO re-assess how to best assign base stats, here is just completely random
            # TODO but i left price using stats calculated via waifu rank, since that seemed fine
            self.claim.attack = random.randint(0, 100)
            self.claim.defense = random.randint(0, 100)
            self.claim.health = random.randint(0, 100)
            self.claim.speed = random.randint(0, 100)
            self.claim.magic = random.randint(0, 100)
            await reql_helpers.set_waifu_claim(self.claim)

            waifu = await reql_helpers.get_waifu_core(self.claim.slug)

            confirmation_embed = disnake.Embed(
                description=f"Successfully rerolled skills for **__{waifu.name}__**!",
                color=disnake.Color.green()
            )
            confirmation_embed.add_field(name=f"New Skills ({self.claim.stats_str()})", value=self.claim.skill_str())

            logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                        f"{inter.channel.name}[{inter.channel.id}] | "
                        f"{inter.author}[{inter.author.id}] | "
                        f"Rerolled skills {self.claim.slug}[{self.claim.id}]")

        await inter.response.edit_message(embeds=[self.message.embeds[0], confirmation_embed], view=None)

    @disnake.ui.button(label="Cancel", emoji="✖️", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        cancel_embed = disnake.Embed(
            description=f"Re-skill cancelled.\n",
            color=disnake.Color.red()
        )
        
        await inter.response.edit_message(embeds=[self.message.embeds[0], cancel_embed], view=None)
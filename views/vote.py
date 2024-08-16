import disnake

import models
from helpers import Mongo

mongo = Mongo()

class WarVoteView(disnake.ui.View):
    def __init__(self, battle: models.Battle) -> None:
        super().__init__(timeout=None)
        self.battle = battle
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        await mongo.fetch_and_delete_vote(interaction.author, self.battle.id)
        return await super().interaction_check(interaction)
    
    @disnake.ui.button(emoji="🗳️", style=disnake.ButtonStyle.red)
    async def vote_red(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        vote = models.Vote(
            battle_id=self.battle.id,
            waifu_vote_id=self.battle.waifu_red_id,
            user_id=inter.author.id,
            timestamp=disnake.utils.utcnow()
        )
        await mongo.insert_vote(vote)

        claim = await mongo.fetch_claim(vote.waifu_vote_id)
        waifu = await mongo.fetch_waifu(claim.slug)

        embed = disnake.Embed(
            title="Thanks for voting!",
            description=f"You have voted for **__{waifu.name}__**!",
            color=disnake.Color.red()
        ).set_thumbnail(url=claim.image_url)
        
        return await inter.response.send_message(embed=embed, ephemeral=True)
    
    @disnake.ui.button(emoji="🗳️", style=disnake.ButtonStyle.blurple)
    async def vote_blue(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        vote = models.Vote(
            battle_id=self.battle.id,
            waifu_vote_id=self.battle.waifu_blue_id,
            user_id=inter.author.id,
            timestamp=disnake.utils.utcnow()
        )
        await mongo.insert_vote(vote)

        claim = await mongo.fetch_claim(vote.waifu_vote_id)
        waifu = await mongo.fetch_waifu(claim.slug)

        embed = disnake.Embed(
            title="Thanks for voting!",
            description=f"You have voted for **__{waifu.name}__**!",
            color=disnake.Color.blue()
        ).set_thumbnail(url=claim.image_url)

        return await inter.response.send_message(embed=embed, ephemeral=True)

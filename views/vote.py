import uuid
import logging

import disnake

from models import Battle, Vote
from helpers import Mongo

logger = logging.getLogger("nyahbot")
mongo = Mongo()

class WarVoteView(disnake.ui.View):
    def __init__(self, battle: Battle) -> None:
        super().__init__(timeout=None)
        self.battle = battle
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        r.db("wars") \
            .table("votes") \
            .filter(
                r.and_(
                    r.row["battle_id"].eq(self.battle.id),
                    r.row["user_id"].eq(str(interaction.author.id))
                )
            ) \
            .delete() \
            .run(conn)
        return await super().interaction_check(interaction)
    
    @disnake.ui.button(emoji="🗳️", custom_id="vote_red_button",
                        style=disnake.ButtonStyle.red)
    async def vote_red(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        vote = Vote(
            id=uuid.uuid4(),
            battle_id=self.battle.id,
            waifu_vote_id=self.battle.waifu_red_id,
            user_id=str(inter.author.id),
            timestamp=disnake.utils.utcnow()
        )
        await vote.insert()

        claim = await mongo.fetch_claim(claim.id)
        waifu = await mongo.fetch_waifu(claim.slug)

        embed = disnake.Embed(
            title="Thanks for voting!",
            description=f"You have voted for **__{waifu.name}__**!",
            color=disnake.Color.red()
        ).set_thumbnail(url=claim.image_url)
        
        return await inter.response.send_message(embed=embed, ephemeral=True)
    
    @disnake.ui.button(emoji="🗳️", custom_id="vote_blue_button",
                        style=disnake.ButtonStyle.blurple)
    async def vote_blue(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        vote = Vote(
            battle_id=self.battle.id,
            waifu_vote_id=self.battle.waifu_blue_id,
            user_id=str(inter.author.id),
            timestamp=disnake.utils.utcnow()
        )
        await vote.insert()

        claim = await mongo.fetch_claim(claim.id)
        waifu = await mongo.fetch_waifu(claim.slug)

        embed = disnake.Embed(
            title="Thanks for voting!",
            description=f"You have voted for **__{waifu.name}__**!",
            color=disnake.Color.blue()
        ).set_thumbnail(url=claim.image_url)

        return await inter.response.send_message(embed=embed, ephemeral=True)
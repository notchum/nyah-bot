import disnake
from rethinkdb import r

from nyahbot.util.globals import conn
from nyahbot.util.dataclasses import (
    Waifu,
    Claim,
    Battle,
    Vote,
)

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
            id=r.uuid().run(conn),
            battle_id=self.battle.id,
            waifu_vote_id=self.battle.waifu_red_id,
            user_id=str(inter.author.id),
            timestamp=disnake.utils.utcnow()
        )
        r.db("wars").table("votes").insert(vote.__dict__).run(conn)

        result = r.db("waifus").table("claims").get(vote.waifu_vote_id).run(conn)
        claim = Claim(**result)
        result = r.db("waifus").table("core").get(claim.slug).run(conn)
        waifu = Waifu(**result)

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
            id=r.uuid().run(conn),
            battle_id=self.battle.id,
            waifu_vote_id=self.battle.waifu_blue_id,
            user_id=str(inter.author.id),
            timestamp=disnake.utils.utcnow()
        )
        r.db("wars").table("votes").insert(vote.__dict__).run(conn)

        result = r.db("waifus").table("claims").get(vote.waifu_vote_id).run(conn)
        claim = Claim(**result)
        result = r.db("waifus").table("core").get(claim.slug).run(conn)
        waifu = Waifu(**result)

        embed = disnake.Embed(
            title="Thanks for voting!",
            description=f"You have voted for **__{waifu.name}__**!",
            color=disnake.Color.blue()
        ).set_thumbnail(url=claim.image_url)

        return await inter.response.send_message(embed=embed, ephemeral=True)
import uuid

import disnake

import models
from helpers import Mongo, WaifuClaimEmbed
from utils.constants import Emojis

mongo = Mongo()

class CharacterDropdown(disnake.ui.StringSelect["CharacterSelectView"]):
    def __init__(self, harem: models.Harem):
        options = [
            disnake.SelectOption(label=claim.name, value=str(claim.id))
            for claim in harem
        ]
        super().__init__(placeholder="Select one of your characters", options=options)
        self.harem = harem

    async def callback(self, inter: disnake.MessageInteraction):
        choice = self.values[0]
        selected_claim_id = uuid.UUID(choice)
        for claim in self.harem:
            if claim.id == selected_claim_id:
                self.view.confirm.disabled = False
                self.view.current_claim = claim
                self.placeholder = f"Are you sure you want to select {claim.name} [{claim.base_stats} BS]?"
                
                waifu = await mongo.fetch_waifu(claim.slug)
                await inter.response.edit_message(
                    embeds=[inter.message.embeds[0], WaifuClaimEmbed(waifu, claim)],
                    view=self.view
                )
                
                break


class CharacterSelectView(disnake.ui.View):
    message: disnake.Message
    selected_claim: models.Claim

    def __init__(self, author: disnake.User | disnake.Member, harem: models.Harem):
        super().__init__()
        self.author = author
        self.harem = harem
        self.current_claim = None

        self.add_item(CharacterDropdown(self.harem))
        self.confirm.disabled = True
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)
        await super().on_timeout()

    @disnake.ui.button(label="Confirm", emoji=Emojis.CHECK_MARK, style=disnake.ButtonStyle.green, row=1)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.selected_claim = self.current_claim
        await interaction.response.edit_message(view=None)
        self.stop()

    @disnake.ui.button(label="Cancel", emoji=Emojis.CROSS_MARK, style=disnake.ButtonStyle.red, row=1)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        embed = disnake.Embed(
            description="Cancelled",
            color=disnake.Color.red()
        )
        await interaction.response.edit_message(
            embeds=[interaction.message.embeds[0], embed],
            view=None
        )
        self.stop()

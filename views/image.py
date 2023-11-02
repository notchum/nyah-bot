import logging
from typing import List

import disnake

from models import Claim
from helpers import Mongo
from utils import Emojis

logger = logging.getLogger("nyahbot")
mongo = Mongo()

class WaifuImageSelectView(disnake.ui.View):
    def __init__(self, embeds: List[disnake.Embed], claim: Claim, author: disnake.User | disnake.Member, reference_view: disnake.ui.View) -> None:
        super().__init__()
        self.embeds = embeds
        self.claim = claim
        self.author = author
        self.reference_view = reference_view

        self.embed_index = 0
        self.prev_page.disabled = True
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(emoji=Emojis.PREV_PAGE)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index -= 1
        current_embed = self.embeds[self.embed_index]

        self.next_page.disabled = False
        if self.embed_index == 0:
            self.prev_page.disabled = True
        
        self.title.label = f"Image {self.embed_index+1} of 4"
        
        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(emoji=Emojis.NEXT_PAGE)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index += 1
        current_embed = self.embeds[self.embed_index]

        self.prev_page.disabled = False
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        
        self.title.label = f"Image {self.embed_index+1} of 4"
        
        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(label="Image 1 of 4", style=disnake.ButtonStyle.primary, disabled=True)
    async def title(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        pass
    
    @disnake.ui.button(label="Select Image", emoji="✔️", style=disnake.ButtonStyle.green, row=1)
    async def choose_image(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        
        self.claim.image_url = current_embed.image.url
        await mongo.update_claim(self.claim)
        
        logger.info(f"{interaction.guild.name}[{interaction.guild.id}] | "
                    f"{interaction.channel.name}[{interaction.channel.id}] | "
                    f"{interaction.author}[{interaction.author.id}] | "
                    f"Selected image {current_embed.image.url} for {self.claim.slug}[{self.claim.id}]")
        
        self.reference_view.embeds[self.reference_view.embed_index] = current_embed
        
        await interaction.response.edit_message(
            content=f"✅ **Successfully chose new image for __{current_embed.title}__** ✅",
            embed=current_embed,
            view=self.reference_view
        )
    
    @disnake.ui.button(label="Cancel", emoji="✖️", style=disnake.ButtonStyle.red, row=1)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        for current_embed in reversed(self.embeds):
            if current_embed.image.url == self.claim.image_url:
                break
        
        await interaction.response.edit_message(embed=current_embed, view=self.reference_view)
import logging
from typing import List

import disnake

from utils import Emojis

logger = logging.getLogger("nyahbot")

class WaifuPaginator(disnake.ui.View):
    message: disnake.Message

    def __init__(self, embeds: List[disnake.Embed], author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.embeds = embeds
        self.author = author

        self.embed_index = 0
        self.prev_page.disabled = True
        self.first_page.disabled = True
        if len(self.embeds) == 1:
            self.next_page.disabled = True
            self.last_page.disabled = True
        else:
            self.next_page.disabled = False
            self.first_page.disabled = False

        # Sets the footer of the embeds with their respective page numbers.
        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {i + 1} of {len(self.embeds)}")     
    
    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id
    
    @disnake.ui.button(emoji=Emojis.FIRST_PAGE, style=disnake.ButtonStyle.blurple)
    async def first_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index = 0
        embed = self.embeds[self.embed_index]
        embed.set_footer(text=f"Page 1 of {len(self.embeds)}")

        self.first_page.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = False
        self.last_page.disabled = False
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji=Emojis.PREV_PAGE)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index -= 1
        embed = self.embeds[self.embed_index]

        self.next_page.disabled = False
        self.last_page.disabled = False
        if self.embed_index == 0:
            self.prev_page.disabled = True
            self.first_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji=Emojis.NEXT_PAGE)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index += 1
        embed = self.embeds[self.embed_index]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji=Emojis.LAST_PAGE, style=disnake.ButtonStyle.blurple)
    async def last_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index = len(self.embeds) - 1
        embed = self.embeds[self.embed_index]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
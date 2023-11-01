import logging
from typing import List

import disnake

from models import Claim
from helpers import Mongo
from utils import Emojis

logger = logging.getLogger("nyahbot")
mongo = Mongo()

class WaifuDexView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, embeds: List[disnake.Embed], author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.embeds = embeds
        self.author = author

        self.current_claims = None
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
            embed.set_footer(text=f"Claimed 0 times  •  Character {i + 1} of {len(self.embeds)}")
    
    @classmethod
    async def create_instance(cls, embeds: List[disnake.Embed], author: disnake.User | disnake.Member):
        instance = cls(embeds, author)
        if await instance.author_claimed_before(embeds[0]):
            instance.change_image.disabled = False
        else:
            instance.change_image.disabled = True
        return instance
    
    async def initialize_footers(self) -> None:
        for i, embed in enumerate(self.embeds):
            num_claims = len(await self.author_claimed_before(embed))
            embed.set_footer(text=f"Claimed {num_claims} times • Character {i + 1} of {len(self.embeds)}")

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id
    
    async def author_claimed_before(self, embed: disnake.Embed) -> List[Claim]:
        slug = embed.url.split("/")[-1].strip()
        return await mongo.fetch_claims_by_slug(self.author, slug)
    
    @disnake.ui.button(emoji=Emojis.FIRST_PAGE, style=disnake.ButtonStyle.blurple)
    async def first_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index = 0
        current_embed = self.embeds[self.embed_index]

        self.first_page.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = False
        self.last_page.disabled = False

        self.current_claims = await self.author_claimed_before(current_embed)
        if self.current_claims:
            self.change_image.disabled = False
        else:
            self.change_image.disabled = True

        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(emoji=Emojis.PREV_PAGE)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index -= 1
        current_embed = self.embeds[self.embed_index]

        self.next_page.disabled = False
        self.last_page.disabled = False
        if self.embed_index == 0:
            self.prev_page.disabled = True
            self.first_page.disabled = True
        
        self.current_claims = await self.author_claimed_before(current_embed)
        if self.current_claims:
            self.change_image.disabled = False
        else:
            self.change_image.disabled = True

        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(emoji=Emojis.NEXT_PAGE)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index += 1
        current_embed = self.embeds[self.embed_index]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True
        
        self.current_claims = await self.author_claimed_before(current_embed)
        if self.current_claims:
            self.change_image.disabled = False
        else:
            self.change_image.disabled = True

        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(emoji=Emojis.LAST_PAGE, style=disnake.ButtonStyle.blurple)
    async def last_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index = len(self.embeds) - 1
        current_embed = self.embeds[self.embed_index]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True

        self.current_claims = await self.author_claimed_before(current_embed)
        if self.current_claims:
            self.change_image.disabled = False
        else:
            self.change_image.disabled = True

        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(label="View Your Image", row=1)
    async def change_image(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        current_embed.set_image(url=self.current_claims[0].image_url)

        self.change_image.disabled = True
        
        await interaction.response.edit_message(embed=current_embed, view=self)
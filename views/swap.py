import copy
from typing import List

import disnake

import utils
from helpers import Mongo
from utils.constants import Emojis

mongo = Mongo()

class SwapDropdown(disnake.ui.StringSelect["WaifuSwapView"]):
    def __init__(self):
        options = []

        for item in utils.items.SHOP_ITEMS:
            options.append(
                disnake.SelectOption(
                    label=item.name,
                    emoji=item.emoji,
                    description=f"Price: {item.price:,}",
                    value=item.type.value
                )
            )

        super().__init__(
            placeholder="Select an item to buy",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        self.view.stop()
        choice = self.values[0]

        await inter.response.edit_message(f"You chose {choice}", view=None)

class WaifuSwapView(disnake.ui.View):
    def __init__(self, embeds: List[disnake.Embed], embed_index: int, author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.embeds = embeds
        self.embed_index = embed_index
        self.original_author = author
        self.reference_view = reference_view
        
        self.selected_index = self.embed_index
        if self.embed_index == 0:
            self.prev_page.disabled = True
        elif self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        self.confirm.disabled = True

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

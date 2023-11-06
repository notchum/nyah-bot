from typing import List

import disnake

from utils import Emojis
import utils.items

class ShopDropdown(disnake.ui.StringSelect["ShopView"]):
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

class ShopView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, author: disnake.User | disnake.Member):
        super().__init__()
        self.author = author

        self.add_item(ShopDropdown())

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.user.id == self.author.id
    
    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

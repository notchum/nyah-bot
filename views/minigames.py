import random
import logging
from typing import List

import disnake

from helpers import Mongo

logger = logging.getLogger("nyahbot")
mongo = Mongo()

class MinigameButton(disnake.ui.Button):
    def __init__(self, label: str, row:int):
        super().__init__(
            label=label,
            row=row
        )

    async def callback(self, inter: disnake.MessageInteraction):
        view = self.view
        if view.answer == self.label:
            view.author_won = True
        else:
            view.author_won = False
        view.stop()

class WaifuSmashOrPassView(disnake.ui.View):
    children: List[MinigameButton]
    
    def __init__(self, author: disnake.User | disnake.Member, answer: str) -> None:
        super().__init__()
        self.original_author = author
        self.answer = answer
        self.author_won = None

        self.add_item(MinigameButton(label="SMASH", row=0))
        self.add_item(MinigameButton(label="PASS", row=0))
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

class WaifuNameGuessView(disnake.ui.View):
    children: List[MinigameButton]

    def __init__(self, author: disnake.User | disnake.Member, answer: str) -> None:
        super().__init__()
        self.original_author = author
        self.answer = answer
        self.author_won = None

        num_buttons = 3
        num_buttons_per_row = 3

        async def fetch_and_shuffle_choices() -> List[str]:
            result = await mongo.fetch_random_waifus(num_buttons - 1, {"name": {"$ne": answer}})
            choices = [waifu.name for waifu in result]
            choices.append(answer)
            random.shuffle(choices)
            return choices

        async def initialize():
            choices = await fetch_and_shuffle_choices()
            row = 0
            for i, choice in enumerate(choices, 1):
                self.add_item(MinigameButton(label=choice, row=row))
                if i % num_buttons_per_row == 0:
                    row += 1

        # You need to call the async initialize function here using an event loop
        # import asyncio
        # asyncio.get_event_loop().run_until_complete(initialize())
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

class WaifuBustGuessView(disnake.ui.View):
    children: List[MinigameButton]

    def __init__(self, author: disnake.User | disnake.Member, answer: str) -> None:
        super().__init__()
        self.original_author = author
        self.answer = answer
        self.author_won = None

        num_buttons = 3
        num_buttons_per_row = 3

        async def fetch_and_shuffle_choices() -> List[str]:
            result = await mongo.fetch_random_waifus(num_buttons - 1, {"bust": {"$ne": answer}})
            choices = [waifu.bust for waifu in result]
            choices.append(answer)
            random.shuffle(choices)
            return choices

        async def initialize():
            choices = await fetch_and_shuffle_choices()
            row = 0
            for i, choice in enumerate(choices, 1):
                self.add_item(MinigameButton(label=choice, row=row))
                if i % num_buttons_per_row == 0:
                    row += 1
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id
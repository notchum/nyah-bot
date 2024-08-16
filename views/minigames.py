import random
from typing import List

import disnake

from helpers import Mongo

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
    message: disnake.Message
    
    def __init__(self, author: disnake.User | disnake.Member, answer: str) -> None:
        super().__init__(timeout=10.5)
        self.original_author = author
        self.answer = answer
        self.author_won = None

        self.add_item(MinigameButton(label="SMASH", row=0))
        self.add_item(MinigameButton(label="PASS", row=0))
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id
    
    async def on_timeout(self) -> None:
        self.author_won = False
        await self.message.edit(view=None)

class WaifuNameGuessView(disnake.ui.View):
    children: List[MinigameButton]
    message: disnake.Message

    def __init__(self, author: disnake.User | disnake.Member, answer: str) -> None:
        super().__init__(timeout=10.5)
        self.original_author = author
        self.answer = answer
        self.author_won = None

    @classmethod
    async def create(cls, author: disnake.User | disnake.Member, answer: str) -> None:
        self = WaifuBustGuessView(author, answer)

        num_buttons = 3
        num_buttons_per_row = 3

        result = await mongo.fetch_random_waifus(
            number=num_buttons - 1,
            aggregations=[
                {"$match": {
                    "name": {"$nin": [answer, None]},
                    "popularity_rank": {"$lt": 600}
                }}
            ]
        )
        
        choices = [waifu.name for waifu in result]
        choices.append(answer)
        random.shuffle(choices)

        row = 0
        for i, choice in enumerate(choices, 1):
            self.add_item(MinigameButton(label=choice, row=row))
            if i % num_buttons_per_row == 0:
                row += 1
        
        return self
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

    async def on_timeout(self) -> None:
        self.author_won = False
        await self.message.edit(view=None)

class WaifuBustGuessView(disnake.ui.View):
    children: List[MinigameButton]
    message: disnake.Message

    def __init__(self, author: disnake.User | disnake.Member, answer: str) -> None:
        super().__init__(timeout=10.5)
        self.original_author = author
        self.answer = answer
        self.author_won = None

    @classmethod
    async def create(cls, author: disnake.User | disnake.Member, answer: str) -> None:
        self = WaifuBustGuessView(author, answer)

        num_buttons = 3
        num_buttons_per_row = 3

        result = await mongo.fetch_random_waifus(
            number=num_buttons - 1,
            aggregations=[
                {"$match": {
                    "bust": {"$nin": [answer, None]},
                    "popularity_rank": {"$lt": 600}
                }}
            ]
        )
        choices = [waifu.bust for waifu in result]
        choices.append(answer)
        random.shuffle(choices)

        row = 0
        for i, choice in enumerate(choices, 1):
            self.add_item(MinigameButton(label=choice, row=row))
            if i % num_buttons_per_row == 0:
                row += 1
        
        return self
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

    async def on_timeout(self) -> None:
        self.author_won = False
        await self.message.edit(view=None)

class WaifuAgeGuessView(disnake.ui.View):
    children: List[MinigameButton]
    message: disnake.Message

    def __init__(self, author: disnake.User | disnake.Member, answer: str) -> None:
        super().__init__(timeout=10.5)
        self.original_author = author
        self.answer = answer
        self.author_won = None

    @classmethod
    async def create(cls, author: disnake.User | disnake.Member, answer: str) -> None:
        self = WaifuAgeGuessView(author, answer)

        num_buttons = 3
        num_buttons_per_row = 3

        result = await mongo.fetch_random_waifus(
            number=num_buttons - 1,
            aggregations=[
                {"$match": {
                    "age": {"$nin": [answer, None]},
                    "popularity_rank": {"$lt": 600}
                }}
            ]
        )
        choices = [waifu.age for waifu in result]
        choices.append(answer)
        random.shuffle(choices)

        row = 0
        for i, choice in enumerate(choices, 1):
            self.add_item(MinigameButton(label=choice, row=row))
            if i % num_buttons_per_row == 0:
                row += 1
        
        return self
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

    async def on_timeout(self) -> None:
        self.author_won = False
        await self.message.edit(view=None)

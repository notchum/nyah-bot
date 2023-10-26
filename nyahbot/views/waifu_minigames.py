import random
from typing import List

import disnake
from rethinkdb import r
from loguru import logger

from nyahbot.util.globals import conn

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
        choices = r.db("waifus") \
                    .table("core") \
                    .filter(
                        r.row["name"].ne(answer)
                    ) \
                    .sample(num_buttons - 1) \
                    .get_field("name") \
                    .run(conn)
        choices.append(answer)
        random.shuffle(choices)
            
        row = 0
        num_buttons_per_row = 3
        for i, choice in enumerate(choices, 1):
            self.add_item(MinigameButton(label=choice, row=row))
            if i % num_buttons_per_row == 0:
                row += 1
    
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
        choices = r.db("waifus") \
                    .table("core") \
                    .has_fields("bust") \
                    .filter(
                        r.row["bust"].ne(answer)
                    ) \
                    .sample(num_buttons - 1) \
                    .get_field("bust") \
                    .run(conn)
        choices.append(answer)
        random.shuffle(choices)
            
        row = 0
        num_buttons_per_row = 3
        for i, choice in enumerate(choices, 1):
            self.add_item(MinigameButton(label=choice, row=row))
            if i % num_buttons_per_row == 0:
                row += 1
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id
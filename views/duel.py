import random
from typing import List
from enum import Enum

import disnake
import models
from utils.constants import Emojis

embed_colors = {
    -3: disnake.Color.dark_red(),
    -2: disnake.Color.red(),
    -1: disnake.Color.orange(),
    0: disnake.Color.yellow(),
    1: disnake.Color.from_rgb(56, 93, 56), # light green
    2: disnake.Color.green(),
    3: disnake.Color.dark_green()
}

class DuelButton(disnake.ui.Button["WaifuDuelView"]):
    def __init__(self, emoji: str, row:int, value: bool):
        super().__init__(
            style=disnake.ButtonStyle.grey,
            emoji=emoji,
            row=row
        )
        self.value = value

    async def callback(self, inter: disnake.MessageInteraction):
        view = self.view
        view.author_choices.append(self.value)
        self.disabled = True

        # Change button color
        if self.value == True:
            self.style = disnake.ButtonStyle.green
        elif self.value == False:
            self.style = disnake.ButtonStyle.red

        # Check if the duel is over
        if view.is_complete():
            for child in view.children:
                child.disabled = True
            view.stop()
            view.is_stopped = True
        elif self.value == True:
            await view.highlight_bad_button()
            
        await inter.response.edit_message(embed=view.embed, view=view)

class WaifuDuelView(disnake.ui.View):
    children: List[DuelButton]
    message: disnake.Message
    
    def __init__(self, embed: disnake.Embed, author: disnake.User | disnake.Member, duel_choices: List[bool]) -> None:
        super().__init__()
        self.embed = embed
        self.author = author
        self.author_choices = []
        self.sum_count = 0
        self.author_won = None
        self.is_stopped = False

        buttons_info = [
            {
                "label": "Love Hotel",
                "emoji": "🏩"
            },
            {
                "label": "Third Impact",
                "emoji": "<:planning:1164258085385293985>"
            },
            {
                "label": "Nosebleed",
                "emoji": "<:nosebleed:1164257425273126953>"
            },
        ]

        button_emojis = [
            "🏩",
            "✨",
            "💖",
            "<:planning:1164258085385293985>",
            "<:nosebleed:1164257425273126953>",
            "<:shinjiHappy:1158460860302377031>",
        ]
        random.shuffle(button_emojis)

        row = 0
        num_buttons_per_row = 3
        for i, emoji in enumerate(button_emojis, 1):
            self.add_item(item=DuelButton(emoji, row, duel_choices.pop()))
            if i % num_buttons_per_row == 0:
                row += 1
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id
    
    async def on_timeout(self) -> None:
        if self.is_stopped:
            return

        # If there wasn't enough selected, then randomly select the rest
        if len(self.author_choices) < 3:
            while len(self.author_choices) < 3:
                random_child = self.select_random_child()
                if random_child:
                    if random_child.value == True:
                        random_child.style = disnake.ButtonStyle.green
                    elif random_child.value == False:
                        random_child.style = disnake.ButtonStyle.red

                    self.author_choices.append(random_child.value)
        
        self.is_complete() # disregard return value since we know its complete
        for child in self.children:
            child.disabled = True
        self.stop()
        
        await self.message.edit(view=self)
        
        return await super().on_timeout()

    def sum_choices(self) -> None:
        t_cnt = self.author_choices.count(True)
        f_cnt = self.author_choices.count(False)
        self.sum_count = t_cnt - f_cnt

    def is_complete(self) -> bool | None:
        self.sum_choices()
        self.embed.color = embed_colors[self.sum_count]
        
        if len(self.author_choices) == 3:
            if self.sum_count > 0:
                self.author_won = True
            else:
                self.author_won = False
            return True 
        else:
            return False
    
    def select_random_child(self, value: bool = None) -> DuelButton | None:
        if value == None:
            check_value = [True, False]
        else:
            check_value = [value]
        
        # Create a list of non-disabled children
        non_disabled_children = [child for child in self.children if not child.disabled and child.value in check_value]

        # Shuffle the list to randomize the selection
        random.shuffle(non_disabled_children)

        # Pick the first child from the shuffled list
        if non_disabled_children:
            return non_disabled_children[0]
        return None
    
    async def highlight_bad_button(self) -> None:
        random_child = self.select_random_child(False)
        if random_child:
            random_child.style = disnake.ButtonStyle.red
        await self.message.edit(view=self)


class MoveTypes(Enum):
    MOVE_ATTACK  = 1
    MOVE_DEFEND  = 2
    MOVE_SPECIAL = 3
    MOVE_SWAP    = 4


class DuelView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, author: disnake.User | disnake.Member, player_harem: models.Harem, opponent_harem: models.Harem) -> None:
        super().__init__()
        self.author = author
        self.player_harem = player_harem
        self.opponent_harem = opponent_harem

        self.turn_num = 1
        self.player_active_claim = random.choice(self.player_harem)
        self.opponent_active_claim = random.choice(self.opponent_harem)
        self.player_move = None
        self.opponent_move = None
        self.player_goes_first = False
        if self.check_speed():
            self.player_goes_first = True

    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    async def on_timeout(self) -> None:
        return await super().on_timeout()
    
    async def check_speed(self) -> bool:
        """Returns true if player is faster"""
        if self.player_active_claim.speed >= self.opponent_active_claim:
            return True
        return False
    
    async def choose_opponent_action(self):
        # if self.opponent_active_claim.trait and oppenent_trait_available:
            # add trait move to selection pool
        # random.choice(move_types)
        return
    
    async def calculate_damage(self):
        match self.player_move:
            case MoveTypes.MOVE_ATTACK:
                return
            case MoveTypes.MOVE_DEFEND:
                return
            case MoveTypes.MOVE_SPECIAL:
                return
            case MoveTypes.MOVE_SWAP:
                return
            case _:
                raise ValueError("TODO: put an error message here")

    async def check_faint(self):
        if self.player_active_claim.health_points = 0:
            self.player_active_claim = self.pick_random_claim(self.player_harem)
        return
    
    async def check_remaining_claims(self):
        return
    
    async def pick_random_claim(self, harem: models.Harem):
        # pick a claim from the harem that hasnt fainted at random
        return

    @disnake.ui.button(label="Attack", emoji=Emojis.SKILL_ATTACK)
    async def attack(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.edit_original_response(content="attack pressed")
    
    @disnake.ui.button(label="Defend", emoji=Emojis.SKILL_DEFENSE)
    async def defend(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.edit_original_response(content="defend pressed")
    
    @disnake.ui.button(label="Special", emoji=Emojis.SKILL_MAGIC, row=1)
    async def special(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.edit_original_response(content="special pressed")

    @disnake.ui.button(label="Swap", emoji=Emojis.SWAP, row=1)
    async def swap(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.edit_original_response(content="swap pressed")

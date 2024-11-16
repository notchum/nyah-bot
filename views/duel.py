import random
from typing import List, Optional
from enum import Enum

import disnake
import models
from utils.constants import Emojis

from bot import NyahBot

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


class BattleResult:
    def __init__(self, damage: int, description: str):
        self.damage = damage
        self.description = description

class DuelView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, bot: NyahBot, author: disnake.User | disnake.Member, player_harem: models.Harem, opponent_harem: models.Harem) -> None:
        super().__init__(timeout=180)  # 3 minute timeout
        self.bot = bot
        self.author = author
        self.player_harem = player_harem
        self.opponent_harem = opponent_harem
        
        # Battle state
        self.turn_num = 1
        self.player_active_claim = random.choice([claim for claim in self.player_harem if claim.health_points > 0])
        self.opponent_active_claim = random.choice([claim for claim in self.opponent_harem if claim.health_points > 0])
        self.player_move = None
        self.opponent_move = None
        self.player_goes_first = self.check_speed()
        
        # Track special move usage
        self.used_specials = set()  # Store character IDs that have used their special

    async def on_timeout(self) -> None:
        # Disable all buttons when the view times out
        for button in self.children:
            button.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    async def initialize(self):
        await self.update_battle_display()
        
        self.attack.disabled = False
        self.defend.disabled = False
        self.swap.disabled = False
        self.update_special_button_state()

        await self.message.edit(view=self)

    def check_speed(self) -> bool:
        """Returns true if player is faster"""
        return self.player_active_claim.speed >= self.opponent_active_claim.speed

    def update_special_button_state(self):
        """Update the special button's enabled/disabled state based on active character's trait"""
        self.special.disabled = not bool(self.player_active_claim.trait)
    
    async def choose_opponent_action(self) -> MoveTypes:
        """Choose a random valid move for the AI opponent"""
        available_moves = [MoveTypes.MOVE_ATTACK, MoveTypes.MOVE_DEFEND]
        
        # Add MOVE_SPECIAL if the character has a trait and hasn't used it
        if (self.opponent_active_claim.trait and 
            self.opponent_active_claim.id not in self.used_specials):
            available_moves.append(MoveTypes.MOVE_SPECIAL)
        
        # Add MOVE_SWAP if there are other available characters
        available_claims = [c for c in self.opponent_harem if c.health_points > 0 and c != self.opponent_active_claim]
        if available_claims:
            available_moves.append(MoveTypes.MOVE_SWAP)
        
        return random.choice(available_moves)

    async def calculate_damage(self, attacker: models.Claim, defender: models.Claim, move_type: MoveTypes) -> BattleResult:
        """Calculate damage and return a battle result with damage and description"""
        damage = 0
        description = ""
        
        match move_type:
            case MoveTypes.MOVE_ATTACK:
                base_damage = attacker.attack - (defender.defense // 2)
                damage = max(base_damage, 1)  # Ensure at least 1 damage
                description = f"{attacker.name} attacks for {damage} damage!"
                
            case MoveTypes.MOVE_DEFEND:
                # Increase defense for next turn
                attacker.defense *= 1.5  # Temporary buff
                description = f"{attacker.name} takes a defensive stance!"
                
            case MoveTypes.MOVE_SPECIAL:
                if attacker.trait:
                    damage = attacker.magic * 2
                    self.used_specials.add(attacker.id)
                    description = f"{attacker.name} uses their special ability for {damage} damage!"
                
            case MoveTypes.MOVE_SWAP:
                if move_type == MoveTypes.MOVE_SWAP:
                    available_claims = [c for c in (self.opponent_harem if attacker == self.opponent_active_claim else self.player_harem)
                                    if c.health_points > 0 and c != attacker]
                    if available_claims:
                        if attacker == self.opponent_active_claim:
                            self.opponent_active_claim = random.choice(available_claims)
                            description = f"Opponent swaps to {self.opponent_active_claim.name}!"
                        else:
                            # Player swap is handled in the swap button
                            description = f"You swap to {self.player_active_claim.name}!"
        
        return BattleResult(damage, description)

    async def apply_damage(self, target, damage: int):
        """Apply damage to a character and ensure HP doesn't go below 0"""
        target.health_points = max(0, target.health_points - damage)

    async def check_faint(self) -> bool:
        """Check if either active character has fainted and handle switching"""
        if self.player_active_claim.health_points <= 0:
            await self.update_battle_display(
                disnake.Embed(
                    description=f"**{self.player_active_claim.name}** has fainted!",
                    color=disnake.Color.yellow()
                )
            )

            available_claims = [c for c in self.player_harem if c.health_points > 0]
            if available_claims:
                self.player_active_claim = random.choice(available_claims)
                self.update_special_button_state()  # Update button state after forced swap
                return True
        
        if self.opponent_active_claim.health_points <= 0:
            await self.update_battle_display(
                disnake.Embed(
                    description=f"**{self.opponent_active_claim.name}** has fainted!",
                    color=disnake.Color.yellow()
                )
            )

            available_claims = [c for c in self.opponent_harem if c.health_points > 0]
            if available_claims:
                self.opponent_active_claim = random.choice(available_claims)
                return True
        
        return False

    async def check_battle_end(self) -> Optional[str]:
        """Check if the battle has ended and return the result message if it has"""
        player_alive = any(c.health_points > 0 for c in self.player_harem)
        opponent_alive = any(c.health_points > 0 for c in self.opponent_harem)
        
        if not player_alive:
            return "You have been defeated!"
        elif not opponent_alive:
            return "Victory! You have defeated your opponent!"
        return None

    async def update_battle_display(self, extra_embed: disnake.Embed = None):
        """Update the battle display with current state"""
        player_remaining = [c for c in self.player_harem if c.health_points > 0 and c != self.player_active_claim]
        opponent_remaining = [c for c in self.opponent_harem if c.health_points > 0 and c != self.opponent_active_claim]

        # Create embed
        duel_image_url = await self.bot.create_waifu_vs_img(self.player_active_claim, self.opponent_active_claim)
        embed = disnake.Embed(
            description=f"### {self.author.mention} vs. <@{self.opponent_active_claim.user_id}>\n",
            color=disnake.Color.yellow()
        ) \
        .set_image(url=duel_image_url) \
        .add_field(
            name=f"{self.player_active_claim.name} ({self.player_active_claim.skill_str_short})",
            value=f"HP: {self.player_active_claim.health_points}"
        ) \
        .add_field(
            name=f"{self.opponent_active_claim.name} ({self.opponent_active_claim.skill_str_short})",
            value=f"HP: {self.opponent_active_claim.health_points}"
        ) \
        .set_footer(text=f"Remaining Charaters | Your team: {len(player_remaining)} | Opponent's team: {len(opponent_remaining)}")
        
        embeds = [embed]
        if extra_embed:
            embeds.append(extra_embed)

        await self.message.edit(content=None, embeds=embeds, view=self)

    async def process_turn(self, player_move: MoveTypes, inter: disnake.MessageInteraction):
        """Process a full turn of combat"""
        self.player_move = player_move
        self.opponent_move = await self.choose_opponent_action()
        
        # Determine order and process moves
        first = self.player_active_claim if self.player_goes_first else self.opponent_active_claim
        second = self.opponent_active_claim if self.player_goes_first else self.player_active_claim
        first_move = self.player_move if self.player_goes_first else self.opponent_move
        second_move = self.opponent_move if self.player_goes_first else self.player_move
        
        # Process first move
        result1 = await self.calculate_damage(first, second, first_move)
        await self.apply_damage(second, result1.damage)
        
        # Check if battle ended after first move
        if await self.check_faint():
            if battle_end := await self.check_battle_end():
                return await self.end_battle(battle_end)
        
        # Process second move if second character is still alive
        if second.health_points > 0:
            result2 = await self.calculate_damage(second, first, second_move)
            await self.apply_damage(first, result2.damage)
            
            # Check if battle ended after second move
            if await self.check_faint():
                if battle_end := await self.check_battle_end():
                    return await self.end_battle(battle_end)
        
        # Update display with results
        await self.update_battle_display()
        
        self.turn_num += 1

    async def end_battle(self, result_message: str):
        """End the battle and clean up"""
        for button in self.children:
            button.disabled = True
        await self.update_battle_display()
        self.stop()

    @disnake.ui.button(label="Attack", emoji=Emojis.SKILL_ATTACK, disabled=True)
    async def attack(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        await self.process_turn(MoveTypes.MOVE_ATTACK, inter)
    
    @disnake.ui.button(label="Defend", emoji=Emojis.SKILL_DEFENSE, disabled=True)
    async def defend(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        await self.process_turn(MoveTypes.MOVE_DEFEND, inter)
    
    @disnake.ui.button(label="Special", emoji=Emojis.SKILL_MAGIC, disabled=True, row=1)
    async def special(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        if not self.player_active_claim.trait:
            await inter.response.send_message("This character doesn't have a special ability!", ephemeral=True)
            return
        if self.player_active_claim.id in self.used_specials:
            await inter.response.send_message("This character has already used their special ability!", ephemeral=True)
            return
        await self.process_turn(MoveTypes.MOVE_SPECIAL, inter)

    @disnake.ui.button(label="Swap", emoji=Emojis.SWAP, disabled=True, row=1)
    async def swap(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        available_claims = [c for c in self.player_harem 
                          if c.health_points > 0 and c != self.player_active_claim]
        
        if not available_claims:
            await inter.response.send_message("No available characters to swap to!", ephemeral=True)
            return
        
        # Create a select menu for choosing the swap target
        options = [
            disnake.SelectOption(
                label=claim.name,
                description=f"HP: {claim.health_points}",
                value=str(claim.id)
            ) for claim in available_claims
        ]
        
        select = disnake.ui.Select(
            placeholder="Choose a character to swap to",
            options=options
        )
        
        async def select_callback(select_inter: disnake.MessageInteraction):
            await select_inter.response.defer()
            selected_claim = next(c for c in self.player_harem if str(c.id) == select_inter.values[0])
            self.player_active_claim = selected_claim
            self.update_special_button_state()  # Update button state after swap
            await self.process_turn(MoveTypes.MOVE_SWAP, select_inter)
        
        select.callback = select_callback
        view = disnake.ui.View()
        view.add_item(select)
        await inter.response.send_message("Choose a character to swap to:", view=view, ephemeral=True)

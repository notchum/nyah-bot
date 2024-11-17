import asyncio
import random
from typing import List, Optional
from enum import Enum

import disnake
import models
from utils.constants import Emojis

from bot import NyahBot


class MoveTypes(Enum):
    MOVE_ATTACK  = 1
    MOVE_DEFEND  = 2
    MOVE_SPECIAL = 3
    MOVE_SWAP    = 4


class DuelView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, bot: NyahBot, author: disnake.User | disnake.Member, player_harem: models.Harem, opponent_harem: models.Harem) -> None:
        super().__init__(timeout=60)  # 1 minute timeout
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
        self.player_won = None
        
        # Track special move usage
        self.used_specials = set()  # Store character IDs that have used their special

    async def on_timeout(self) -> None:
        self.player_won = False
        self.end_battle()

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    async def initialize(self):
        await self.update_battle_display()
        self.update_button_states(False)
        await self.message.edit(view=self)

    def check_speed(self) -> bool:
        """Returns true if player is faster"""
        return self.player_active_claim.speed >= self.opponent_active_claim.speed

    def update_button_states(self, disabled: bool):
        """Update the special button's enabled/disabled state based on active character's trait"""
        self.attack.disabled = disabled
        self.swap.disabled = disabled
        if disabled:
            self.special.disabled = disabled
        else:
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

    async def calculate_damage(self, attacker: models.Claim, defender: models.Claim, move_type: MoveTypes) -> int:
        """Calculate damage and return a battle result with damage and description"""
        damage = 0
        description = ""
        
        match move_type:
            case MoveTypes.MOVE_ATTACK:
                damage = attacker.attack - defender.defense
                description = f"{attacker.name} attacks for {damage} damage!"
                
            case MoveTypes.MOVE_DEFEND:
                # defend is always immediate. if the attacker has more attack than defense, then
                # the defender doesn't successfully defend and will take the difference in damage
                # but if the attacker has less attack than defense, then the defender will take 0 damage
                # and the attacker will take the difference in 
                # Increase defense for next turn
                attacker.defense *= 1.5  # Temporary buff
                description = f"{attacker.name} takes a defensive stance!"
                
            case MoveTypes.MOVE_SPECIAL:
                if attacker.trait:
                    damage = attacker.attack * 2
                    self.used_specials.add(attacker.id)
                    description = f"{attacker.name} uses their special ability for {damage} damage!"
                
            case MoveTypes.MOVE_SWAP:
                available_claims = [c for c in (self.opponent_harem if attacker == self.opponent_active_claim else self.player_harem)
                                if c.health_points > 0 and c != attacker]
                if available_claims:
                    if attacker == self.opponent_active_claim:
                        self.opponent_active_claim = random.choice(available_claims)
                        description = f"Opponent swaps to {self.opponent_active_claim.name}!"
                    else:
                        # Player swap is handled in the swap button
                        description = f"You swap to {self.player_active_claim.name}!"
        
        return damage

    async def apply_damage(self, target: models.Claim, damage: int):
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

    async def check_battle_end(self) -> bool:
        """Check if the battle has ended and return the result message if it has"""
        player_alive = any(c.health_points > 0 for c in self.player_harem)
        opponent_alive = any(c.health_points > 0 for c in self.opponent_harem)
        
        if not player_alive:
            self.player_won = False
            return True
        elif not opponent_alive:
            self.player_won = True
            return True
        return False

    async def update_battle_display(self, extra_embed: disnake.Embed = None, sleep: bool = False):
        """Update the battle display with current state"""
        # Create embed
        duel_image_url = await self.bot.create_waifu_vs_img(self.player_active_claim, self.opponent_active_claim)
        embed = disnake.Embed(
            description=f"### {self.author.mention} vs. <@{self.opponent_active_claim.user_id}>\n",
            color=disnake.Color.yellow()
        ) \
        .set_image(url=duel_image_url) \
        .add_field(
            name=f"🟥 {self.player_active_claim.name} ({self.player_active_claim.skill_str_short})",
            value=self.player_active_claim.health_bar_str
        ) \
        .add_field(
            name=f"🟦 {self.opponent_active_claim.name} ({self.opponent_active_claim.skill_str_short})",
            value=self.opponent_active_claim.health_bar_str
        ) \
        .set_footer(text=f"Turn {self.turn_num}")
        
        # Get remaining characters
        player_remaining = [c for c in self.player_harem if c.health_points > 0 and c != self.player_active_claim]
        opponent_remaining = [c for c in self.opponent_harem if c.health_points > 0 and c != self.opponent_active_claim]
        self.red.label = f"{len(player_remaining)} remaining"
        self.blue.label = f"{len(opponent_remaining)} remaining"
        
        # Disable the buttons if we are sleeping
        if sleep:
            await self.update_button_states(True)

        # Send the embed(s)
        embeds = [embed]
        if extra_embed:
            embeds.append(extra_embed)
        await self.message.edit(content=None, embeds=embeds, view=self)

        # Sleep for a bit so the user can see the changes
        if sleep:
            await asyncio.sleep(3)

    async def process_turn(self, player_move: MoveTypes):
        """Process a full turn of combat"""
        self.player_move = player_move
        self.opponent_move = await self.choose_opponent_action()
        
        # Determine order and process moves
        first = self.player_active_claim if self.check_speed() else self.opponent_active_claim
        second = self.opponent_active_claim if self.check_speed() else self.player_active_claim
        first_move = self.player_move if self.check_speed() else self.opponent_move
        second_move = self.opponent_move if self.check_speed() else self.player_move
        
        # Process first move
        result1 = await self.calculate_damage(first, second, first_move)
        await self.apply_damage(second, result1.damage)
        
        # Check if battle ended after first move
        if await self.check_faint():
            if await self.check_battle_end():
                return await self.end_battle()
        
        # Process second move if second character is still alive
        if second.health_points > 0:
            result2 = await self.calculate_damage(second, first, second_move)
            await self.apply_damage(first, result2.damage)
            
            # Check if battle ended after second move
            if await self.check_faint():
                if await self.check_battle_end():
                    return await self.end_battle()
        
        # Update display with results
        await self.update_battle_display()
        
        self.turn_num += 1

    async def end_battle(self):
        """End the battle and clean up"""
        await self.message.edit(view=None)
        await self.update_battle_display(
            disnake.Embed(
                description='You won!' if self.player_won else 'You lost!'
            )
        )
        self.stop()

    @disnake.ui.button(label="2 remaining", style=disnake.ButtonStyle.red, disabled=True)
    async def red(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        pass

    @disnake.ui.button(label="2 remaining", style=disnake.ButtonStyle.blurple, disabled=True)
    async def blue(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        pass

    @disnake.ui.button(label="Attack", emoji=Emojis.SKILL_ATTACK, disabled=True, row=1)
    async def attack(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        await self.process_turn(MoveTypes.MOVE_ATTACK)
    
    # @disnake.ui.button(label="Defend", emoji=Emojis.SKILL_DEFENSE, disabled=True)
    # async def defend(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
    #     await inter.response.defer()
    #     await self.process_turn(MoveTypes.MOVE_DEFEND)
    
    @disnake.ui.button(label="Special", emoji=Emojis.SKILL_MAGIC, disabled=True, row=1)
    async def special(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        if not self.player_active_claim.trait:
            await inter.response.send_message("This character doesn't have a special ability!", ephemeral=True)
            return
        if self.player_active_claim.id in self.used_specials:
            await inter.response.send_message("This character has already used their special ability!", ephemeral=True)
            return
        await self.process_turn(MoveTypes.MOVE_SPECIAL)

    @disnake.ui.button(label="Swap", emoji=Emojis.SWAP, disabled=True, row=1)
    async def swap(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        # TODO create a disnake.ui.View for the character select
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
            await self.process_turn(MoveTypes.MOVE_SWAP)
        
        select.callback = select_callback
        select.row = 2
        # view = disnake.ui.View()
        # view.add_item(select)
        # await inter.response.send_message("Choose a character to swap to:", view=view, ephemeral=True)
        self.add_item(select)
        self.update_button_states(True)
        await self.message.edit(view=self)

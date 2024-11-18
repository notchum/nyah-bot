import asyncio
import random
from enum import Enum

import disnake
import models
from loguru import logger
from utils.constants import Emojis

from bot import NyahBot


class MoveTypes(Enum):
    MOVE_ATTACK  = 1
    MOVE_SPECIAL = 2
    MOVE_SWAP    = 3


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
        
        logger.info(f"Initializing duel between {author} and AI opponent")
        logger.debug(f"Initial player character: {self.player_active_claim.name}")
        logger.debug(f"Initial opponent character: {self.opponent_active_claim.name}")

    async def on_timeout(self) -> None:
        logger.info(f"Duel timed out for player {self.author}")
        self.player_won = False
        await self.end_battle()

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    async def initialize(self):
        await self.update_battle_display()
        await self.update_button_states(disabled=False)
        self.message = await self.message.edit(view=self)

    def check_speed(self) -> bool:
        """Returns true if player is faster"""
        is_faster = self.player_active_claim.speed >= self.opponent_active_claim.speed
        logger.debug(f"Speed check: player ({self.player_active_claim.speed}) vs opponent ({self.opponent_active_claim.speed})")
        return is_faster

    async def update_button_states(self, disabled: bool) -> None:
        """
        Disable or enable the attack, special, and swap buttons based on the given boolean.

        If disabled is True, all buttons will be disabled. If disabled is False, the buttons will be
        enabled or disabled based on the following logic:

        - The special button will be enabled if the player's active claim has a trait and hasn't used it yet.
        - The swap button will be enabled if there are other available characters in the player's harem.
        """
        self.attack.disabled = disabled
        if disabled:
            self.special.disabled = disabled
            self.swap.disabled = disabled
        else:
            self.special.disabled = not bool(self.player_active_claim.trait) or self.player_active_claim.id in self.used_specials
            player_remaining = [c for c in self.player_harem if c.health_points > 0 and c != self.player_active_claim]
            self.swap.disabled = not bool(len(player_remaining))
        
        self.message = await self.message.edit(view=self)
        
        logger.debug(f"Updated button states: attack={not self.attack.disabled}, special={not self.special.disabled}, swap={not self.swap.disabled}")
    
    async def handle_character_select(self) -> None:
        # Store the event that will be set when selection is made
        self.character_selected_event = asyncio.Event()
        
        # Get available characters
        available_claims = [
            c for c in self.player_harem 
            if c.health_points > 0 and c != self.player_active_claim
        ]
        
        logger.info(f"Available characters for selection: {[c.name for c in available_claims]}")
        
        # Create select menu options
        options = [
            disnake.SelectOption(
                label=claim.name,
                description=f"HP: {claim.health_points}/{claim.health}",
                value=str(claim.id)
            ) for claim in available_claims
        ]
        
        # Create the select menu
        select = disnake.ui.StringSelect(
            placeholder="Choose a character to swap to",
            options=options
        )
        
        async def select_callback(select_inter: disnake.MessageInteraction):
            await select_inter.response.defer()
            
            # Find the selected character
            selected_claim = next(
                c for c in self.player_harem 
                if str(c.id) == select_inter.values[0]
            )
            
            logger.info(f"Selected character: {selected_claim.name}")
            
            # Update the active claim
            self.player_active_claim = selected_claim
            
            # Remove the select menu
            self.remove_item(select)
            self.message = await self.message.edit(view=self)
            
            # Signal that selection is complete
            self.character_selected_event.set()
        
        # Set up the select menu
        select.callback = select_callback
        select.row = 2
        self.add_item(select)
        self.message = await self.message.edit(view=self)
        
        logger.info("Waiting for character selection...")
        await self.character_selected_event.wait()
        logger.info("Character selection complete.")

    async def choose_opponent_action(self) -> MoveTypes:
        """Choose a random valid move for the AI opponent"""
        available_moves = [MoveTypes.MOVE_ATTACK for _ in range(3)]
        
        # Add MOVE_SPECIAL if the character has a trait and hasn't used it
        if (self.opponent_active_claim.trait and 
            self.opponent_active_claim.id not in self.used_specials):
            available_moves.append(MoveTypes.MOVE_SPECIAL)
        
        # Add MOVE_SWAP if there are other available characters
        available_claims = [c for c in self.opponent_harem if c.health_points > 0 and c != self.opponent_active_claim]
        if available_claims:
            available_moves.append(MoveTypes.MOVE_SWAP)
        
        chosen_move = random.choice(available_moves)
        logger.debug(f"AI opponent chose move: {chosen_move}")
        return chosen_move

    async def check_faint(self) -> bool:
        """Check if either active character has fainted and handle switching"""
        await self.update_battle_display()
        if self.player_active_claim.health_points <= 0:
            faintee = self.player_active_claim
            logger.info(f"Player character {self.player_active_claim.name} has fainted")
            available_claims = [c for c in self.player_harem if c.health_points > 0]
            if available_claims:
                # await self.handle_character_select() # TODO: Figure this out
                self.player_active_claim = random.choice(available_claims)
                await self.send_notification(
                    description=f"**{faintee.name}** has fainted! Switching to **{self.player_active_claim.name}**"
                )
                return True
            await self.send_notification(
                description=f"**{faintee.name}** has fainted! All of your characters have fainted!"
            )
            return True
        
        if self.opponent_active_claim.health_points <= 0:
            faintee = self.opponent_active_claim
            logger.info(f"Opponent character {self.opponent_active_claim.name} has fainted")
            available_claims = [c for c in self.opponent_harem if c.health_points > 0]
            if available_claims:
                self.opponent_active_claim = random.choice(available_claims)
                await self.send_notification(
                    description=f"**{faintee.name}** has fainted! Switching to **{self.opponent_active_claim.name}**"
                )
                return True
            await self.send_notification(
                description=f"**{faintee.name}** has fainted! All of the opponent's characters have fainted!"
            )
            return True
        
        return False

    async def check_battle_end(self) -> bool:
        """Check if the battle has ended"""
        player_alive = any(c.health_points > 0 for c in self.player_harem)
        opponent_alive = any(c.health_points > 0 for c in self.opponent_harem)
        
        if not player_alive or not opponent_alive:
            logger.info(f"Battle ended. Winner: {'player' if opponent_alive else 'opponent'}")
            logger.debug(f"Final state - Player alive: {player_alive}, Opponent alive: {opponent_alive}")
            
            if not player_alive:
                self.player_won = False
            elif not opponent_alive:
                self.player_won = True
            return True
        return False

    async def update_battle_display(self):
        """Update the battle display with the current state"""
        logger.debug(f"Updating battle display for turn {self.turn_num}")
        
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
        logger.debug(f"Remaining characters - Player: {len(player_remaining)}, Opponent: {len(opponent_remaining)}")
        
        self.red.label = f"{len(player_remaining)} remaining"
        self.blue.label = f"{len(opponent_remaining)} remaining"
        
        self.message = await self.message.edit(content=None, embed=embed, view=self)
    
    async def send_notification(self, description: str, title: str = None):
        """Send a notification to the user during the duel

        Parameters
        ----------
            description (str): The description of the notification
            title (str, optional): The title of the notification. Defaults to None.
        """
        # Send the notification embed
        embed = disnake.Embed(
            title=title,
            description=description,
            color=disnake.Color.dark_magenta()
        )
        self.message = await self.message.edit(content=None, embeds=[self.message.embeds[0], embed], view=self)

        # Sleep for a bit so the user can read the notification
        await asyncio.sleep(3)

    async def process_move(self, attacker: models.Claim, defender: models.Claim, move_type: MoveTypes) -> None:
        """Process a single move of a turn"""
        logger.info(f"Processing move: {attacker.name} using {move_type} against {defender.name}")
        
        match move_type:
            case MoveTypes.MOVE_ATTACK:
                damage = attacker.attack
                defender.health_points = max(0, defender.health_points - damage)
                logger.debug(f"Attack dealt {damage} damage. {defender.name} HP: {defender.health_points}")
                await self.send_notification(
                    description=f"**{attacker.name}** attacks for `{damage}` damage!"
                )
                
            case MoveTypes.MOVE_SPECIAL:
                if attacker.trait:
                    damage = attacker.attack * 2 # TODO: Make this dynamic once traits are implemented
                    defender.health_points = max(0, defender.health_points - damage)
                    self.used_specials.add(attacker.id)
                    logger.debug(f"Special attack dealt {damage} damage. {defender.name} HP: {defender.health_points}")
                    await self.send_notification(
                        description=f"**{attacker.name}** uses their special ability for `{damage}` damage!"
                    )
                else:
                    logger.error(f"Attempted to use special move for {attacker.name} without a trait")
                
            case MoveTypes.MOVE_SWAP:
                available_claims = [c for c in (self.opponent_harem if attacker == self.opponent_active_claim else self.player_harem)
                                if c.health_points > 0 and c != attacker]
                if available_claims:
                    if attacker == self.opponent_active_claim:
                        self.opponent_active_claim = random.choice(available_claims)
                        logger.info(f"Opponent swapped to {self.opponent_active_claim.name}")
                        await self.send_notification(
                            description=f"Opponent swaps to **{self.opponent_active_claim.name}**!"
                        )
                    else:
                        # await self.handle_character_select() # TODO: Figure this out
                        self.player_active_claim = random.choice(available_claims)
                        logger.info(f"Player swapped to {self.player_active_claim.name}")
                        await self.send_notification(
                            description=f"You swap to **{self.player_active_claim.name}*!"
                        )
                else:
                    logger.error(f"Attempted to swap with no available claims for {attacker.name}")

    async def process_turn(self, player_move: MoveTypes):
        """Process a full turn of combat"""
        logger.info(f"Processing turn {self.turn_num}")

        # Update button states
        await self.update_button_states(disabled=True)
        
        # Select opponent move
        self.player_move = player_move
        self.opponent_move = await self.choose_opponent_action()
        
        logger.debug(f"Moves selected - Player: {self.player_move}, Opponent: {self.opponent_move}")
        
        # Determine order and process moves
        first = self.player_active_claim if self.check_speed() else self.opponent_active_claim
        second = self.opponent_active_claim if self.check_speed() else self.player_active_claim
        first_move = self.player_move if self.check_speed() else self.opponent_move
        second_move = self.opponent_move if self.check_speed() else self.player_move
        
        logger.debug(f"Turn order: {first.name} ({first_move}) -> {second.name} ({second_move})")
        
        # Process first move
        await self.process_move(first, second, first_move)
        
        # Check if battle ended after first move
        if await self.check_faint():
            if await self.check_battle_end():
                return await self.end_battle()
        
        # Process second move if second character is still alive
        if second.health_points > 0:
            if first_move == MoveTypes.MOVE_SWAP:
                first = self.player_active_claim if first in self.player_harem else self.opponent_active_claim
            await self.process_move(second, first, second_move)
            
            # Check if battle ended after second move
            if await self.check_faint():
                if await self.check_battle_end():
                    return await self.end_battle()
        
        # Advance turn
        logger.debug(f"Turn {self.turn_num} completed")
        self.turn_num += 1
        
        # Update display with results
        await self.update_battle_display()
        await self.update_button_states(disabled=False)

    async def end_battle(self):
        """End the battle and clean up"""
        logger.info(f"Battle ended. Winner: {'player' if self.player_won else 'opponent'}")
        self.message = await self.message.edit(view=None)
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
        await inter.response.defer()
        await self.process_turn(MoveTypes.MOVE_SWAP)

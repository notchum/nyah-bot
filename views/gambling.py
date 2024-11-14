import asyncio
import random
from typing import List

import disnake

import models
from utils.constants import Emojis

class Symbol:
    SEVEN  = "<:Slot_7:1172053243690487808>"
    BAR    = "<:Slot_Bar:1172053260736155648>"
    BELL   = "<:Slot_Bell:1172053214561050625>"
    BLANK  = "<:Slot_Blank:1172366193324204094>"
    CHERRY = "<:Slot_Cherry:1172366208742461440>"
    GRAPE  = "<:Slot_Grapes:1172366211691065384>"
    LEMON  = "<:Slot_Lemon:1172366210306949163>"
    ORANGE = "<:Slot_Orange:1172366212513148980>"

    # CHERRY = "🍒"
    # GRAPE  = "🍇"
    # LEMON = "🍋"
    # ORANGE = "🍊"
    # PINEAPPLE = "🍍"
    # STRAWBERRY = "🍓"
    # WATERMELON = "🍉"
    # BANANA = "🍌"


class SlotMachine:
    class Reel:
        def __init__(self, length: int = 10):
            symbol_list = [Symbol.SEVEN, Symbol.BAR, Symbol.BELL, Symbol.ORANGE,
                           Symbol.CHERRY, Symbol.GRAPE, Symbol.LEMON]

            # Ensure at least 1 orange, 1 cherry, and 1 BAR
            self.symbols = [Symbol.ORANGE]
            while len(self.symbols) < length:
                self.symbols.append(random.choice(symbol_list))

            # Ensure there is at most 2 of each symbol (except orange, which has max 1)
            for symbol in symbol_list:
                if symbol in [Symbol.ORANGE]:
                    max_count = 1
                else:
                    max_count = 2
                while self.symbols.count(symbol) > max_count:
                    index = self.symbols.index(symbol)
                    self.symbols[index] = random.choice([s for s in symbol_list if s != symbol])
            random.shuffle(self.symbols)

        def rotate(self) -> None:
            self.symbols.insert(0, self.symbols.pop())

        def get_face_symbols(self, num_rows: int) -> List[Symbol]:
            return self.symbols[:num_rows]
    
    def __init__(self, player: models.NyahPlayer, num_reels: int = 3, num_rows: int = 3, num_paylines: int = 1):
        if num_reels < 3:
            raise ValueError("Number of reels must be at least 3")
        if num_rows < 3:
            raise ValueError("Number of rows must be at least 3")
        if num_paylines < 1:
            raise ValueError("Number of paylines must be at least 1")
        if num_paylines > num_rows:
            raise ValueError("Number of paylines cannot be greater than number of rows")
        
        self.player = player
        self.num_reels = num_reels
        self.num_rows = num_rows
        self.num_paylines = num_paylines
        
        self.bet = 10
        self.spin_count = 0
        self.payout_count = 0
        self.last_payout = 0
        self.reels = [self.Reel() for _ in range(self.num_reels)]
        self.payline_indices = [i for i in range(self.num_paylines)] if self.num_paylines > 1 else [self.num_rows // 2]
        self.embeds = []

        self.max_bet = 200
        self.min_bet = 10
        self.paytable = {
            # symbol: [1 of a kind, 2 of a kind, 3 of a kind]
            Symbol.CHERRY: [2, 5, 10],
            Symbol.BELL: [0, 0, 10],
            Symbol.BAR: [0, 0, 20],
            Symbol.SEVEN: [0, 0, 30],
            Symbol.LEMON: [0, 0, 40],
            Symbol.GRAPE: [0, 0, 60],
            Symbol.ORANGE: [0, 0, 100]
        }
    
    def spin(self) -> None:
        self.embeds = []

        if self.spin_count > 0:
            self.reels = [self.Reel() for _ in range(self.num_reels)]

        reels_spins = [5 * i + random.randint(0, 10) for i, _ in enumerate(range(self.num_reels), 1)]
        while any(reels_spins):
            for i, reel in enumerate(self.reels):
                if reels_spins[i] == 0:
                    continue
                reel.rotate()
                reels_spins[i] -= 1
            self.embeds.append(self.current_embed)
        self.spin_count += 1
    
    def calculate_payout(self, bet_amount: int) -> int:
        middle_row = [reel.get_face_symbols(self.num_rows)[1] for reel in self.reels]

        symbol_counts = {symbol: middle_row.count(symbol) for symbol in middle_row}

        multiplier = 0
        for symbol, count in symbol_counts.items():
            if symbol not in self.paytable:
                continue
            multiplier = self.paytable[symbol][count - 1]
            if multiplier > 0:
                break

        payout = multiplier * bet_amount

        return payout

    @property
    def current_embed(self) -> disnake.Embed:
        embed = disnake.Embed(description=self.face_str, color=disnake.Color.gold())
        embed.add_field(name="Current Bet", value=f"`{self.bet:,}` {Emojis.TICKET}")
        embed.add_field(name="Current Balance", value=f"`{self.player.money:,}` {Emojis.TICKET}")
        embed.add_field(name="Last Payout", value=f"`{self.last_payout:,}` {Emojis.TICKET}")
        return embed

    @property
    def paytable_embed(self) -> disnake.Embed:
        embed = disnake.Embed(
            title="Paytable",
            description=f"Minimum bet: `{self.min_bet:,}` {Emojis.TICKET}\n"
                        f"Maximum bet: `{self.max_bet:,}` {Emojis.TICKET}",
            color=disnake.Color.dark_teal()
        )
        
        symbol_field = ""
        payout_field = ""
        for symbol, payouts in self.paytable.items():
            for count, payout in enumerate(payouts, 1):
                if payout > 0:
                    symbol_field += f" {symbol} " * count + "\n"
                    payout_field += f"`Bet x {payout}`\n"

        embed.add_field(name="Symbol", value=symbol_field)
        embed.add_field(name="Payout Multiplier", value=payout_field)
        return embed

    @property
    def face_str(self) -> str:
        fmt = ""
        for i in range(self.num_rows):
            if i in self.payline_indices:
                fmt += "`PAY-->` "
            else:
                fmt += "`      ` "
            fmt += " | ".join([reel.get_face_symbols(self.num_rows)[i] for reel in self.reels])
            if i in self.payline_indices:
                fmt += " `<--PAY`\n"
            else:
                fmt += " `      `\n"
        return fmt


class SlotsView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, machine: SlotMachine, author: disnake.User | disnake.Member):
        super().__init__(timeout=30.0)
        self.machine = machine
        self.author = author

        self.decrease_bet.disabled = True
    
    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(label="Spin", emoji="🎰", style=disnake.ButtonStyle.green)
    async def spin(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        
        await self.machine.player.add_user_money(-self.machine.bet)

        self.machine.spin()

        self.view_paytable.label = "View Paytable"
        for child in self.children:
            child.disabled = True
        
        for embed in self.machine.embeds:
            await interaction.edit_original_response(embed=embed, view=self)
            await asyncio.sleep(0.2)

        payout = self.machine.calculate_payout(self.machine.bet)
        self.machine.last_payout = payout
        if payout > 0:
            await self.machine.player.add_user_money(payout)
        
        if self.machine.player.money == 0:
            await interaction.edit_original_response(embed=self.machine.current_embed, view=None)
            return
        
        for child in self.children:
                child.disabled = False

        if self.machine.player.money < self.machine.bet:
            self.machine.bet = self.machine.min_bet
            self.decrease_bet.disabled = True
        elif self.machine.bet == self.machine.max_bet:
            self.increase_bet.disabled = True
            self.decrease_bet.disabled = False
        elif self.machine.bet == self.machine.min_bet:
            self.decrease_bet.disabled = True
            self.increase_bet.disabled = False
        else:
            self.increase_bet.disabled = False
            self.decrease_bet.disabled = False

        await interaction.edit_original_response(embed=self.machine.current_embed, view=self)

    @disnake.ui.button(label="Bet +10", emoji="⬆️")
    async def increase_bet(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.machine.bet += 10
        self.decrease_bet.disabled = False
        if self.machine.bet == self.machine.max_bet or self.machine.player.money == self.machine.bet:
            self.increase_bet.disabled = True
        self.view_paytable.label = "View Paytable"
        await interaction.response.edit_message(embed=self.machine.current_embed, view=self)
    
    @disnake.ui.button(label="Bet -10", emoji="⬇️")
    async def decrease_bet(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.machine.bet -= 10
        self.increase_bet.disabled = False
        if self.machine.bet == self.machine.min_bet:
            self.decrease_bet.disabled = True
        self.view_paytable.label = "View Paytable"
        await interaction.response.edit_message(embed=self.machine.current_embed, view=self)
    
    @disnake.ui.button(label="Max Bet", emoji="⏫")
    async def max_bet(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if self.machine.player.money < self.machine.max_bet:
            self.machine.bet = self.machine.player.money
        else:
            self.machine.bet = self.machine.max_bet
        self.increase_bet.disabled = True
        self.decrease_bet.disabled = False
        self.view_paytable.label = "View Paytable"
        await interaction.response.edit_message(embed=self.machine.current_embed, view=self)

    @disnake.ui.button(label="View Paytable", emoji="💰", style=disnake.ButtonStyle.blurple, row=1)
    async def view_paytable(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if self.view_paytable.label == "Hide Paytable":
            self.view_paytable.label = "View Paytable"
            await interaction.response.edit_message(embed=self.machine.current_embed, view=self)
        else:
            self.view_paytable.label = "Hide Paytable"
            await interaction.response.edit_message(embeds=[self.machine.current_embed, self.machine.paytable_embed], view=self)

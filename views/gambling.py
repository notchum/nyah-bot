import random
from enum import Enum

import disnake

WILD = "🃏"
JACKPOT = "🍀"
BASE_SYMBOLS = ["🍒", "🍊", "🍋", "🍉", "🍇", "🍎"]

class Paytable(Enum):
    TWO_OF_A_KIND = 2
    THREE_OF_A_KIND = 10
    JACKPOT = 100


class SlotMachine:
    class Reel:
        def __init__(self):
            self.symbols = BASE_SYMBOLS + [WILD, JACKPOT]
            random.shuffle(self.symbols)

        def rotate(self) -> None:
            self.symbols.insert(0, self.symbols.pop())

        def get_face_symbols(self, num_rows: int) -> list[str]:
            return self.symbols[:num_rows]
    
    def __init__(self, num_reels: int = 3, num_rows: int = 3, num_paylines: int = 1):
        self.num_reels = num_reels
        self.num_rows = num_rows
        self.num_paylines = num_paylines
        
        self.reels = [self.Reel() for _ in range(self.num_reels)]
        self.embeds = [disnake.Embed(description=self.face_str)]
        self.spins = 0
        self.payouts = 0
    
    def spin(self) -> None:
        reels_spins = [3 * i + random.randint(0, 4) for i, _ in enumerate(range(self.num_reels), 1)]
        while any(reels_spins):
            for i, reel in enumerate(self.reels):
                if reels_spins[i] == 0:
                    continue
                reel.rotate()
                reels_spins[i] -= 1
            self.embeds.append(disnake.Embed(description=self.face_str))
        self.spins += 1
    
    def calculate_payout(self, bet_amount: int) -> int:
        # Extract the symbols from the middle row
        middle_row = [reel.get_face_symbols(self.num_rows)[1] for reel in self.reels]

        # Count the occurrences of each symbol in the middle row
        symbol_counts = {symbol: middle_row.count(symbol) for symbol in middle_row}

        for symbol in BASE_SYMBOLS + [JACKPOT]:
            symbol_count = symbol_counts.get(symbol, 0)
            
            # 2 of a kind with a wild
            if symbol_count == 2 and symbol_counts.get(WILD, 0):
                payout = bet_amount * Paytable.THREE_OF_A_KIND.value
                break
            
            # 2 of a kind
            elif symbol_count == 2 and symbol != WILD:
                payout = bet_amount * Paytable.TWO_OF_A_KIND.value
                break
            
            # 3 of a kind
            elif symbol_count == 3 and symbol not in [WILD, JACKPOT]:
                payout = bet_amount * Paytable.THREE_OF_A_KIND.value
                break

            # jackpot
            elif symbol_count == 3 and symbol == JACKPOT:
                payout = bet_amount * Paytable.JACKPOT.value
                break

            else:
                payout = 0

        # Return the result and balance
        return payout

    @property
    def face_str(self):
        fmt = ""
        for i in range(self.num_rows):
            if round(self.num_rows / 2) == i + 1:
                fmt += "`PAY-->` "
            else:
                fmt += "`      ` "
            fmt += " | ".join([reel.get_face_symbols(self.num_rows)[i] for reel in self.reels]) + "\n"
        return fmt


class SlotsView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, machine: SlotMachine, author: disnake.User | disnake.Member):
        super().__init__(timeout=30.0)
        self.machine = machine
        self.author = author
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(label="Spin", emoji="🎰", style=disnake.ButtonStyle.green)
    async def spin(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.machine.spin()

        self.spin.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()

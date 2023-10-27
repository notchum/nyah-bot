import datetime
from enum import Enum

class Emojis:
    COINS      = "<:coins:1158472639413764178>"
    SWAP       = "<:replace:1158888082343477258>"
    PREV_PAGE  = "<:leftWaifu:1158460793063477420>"
    NEXT_PAGE  = "<:rightWaifu:1158460837359538186>"
    FIRST_PAGE = "<a:remspin:1159723782047551510>"
    LAST_PAGE  = "<a:ramspin:1159723691698044968>"
    CLAIM      = "<a:_:1167319600472531015>"

class MMR(Enum):
    DUEL_LOSS = -15 # gained from losing a duel
    DUEL_WIN  = 15 # gained from winning a duel

class Experience(Enum):
    BASE_LEVEL = 100 # base amount of XP per level
    CLAIM      = 5  # gained from claiming a waifu
    DUEL_WIN   = 12 # gained from winning a duel
    DUEL_LOSS  = 8  # gained from losing a duel
    MINIGAME_WIN  = 4  # gained from beating a minigame
    MINIGAME_LOSS = 2  # gained from losting a minigame
    WAR_ROUND  = 15 # gained from each round of a war
    WAR_WIN    = 50 # gained from winning a war

class Money(Enum):
    PER_LEVEL     = 1000  # gained from leveling up (multiplied by the new level)
    MINIGAME_WIN  = 100   # gained from beating a minigame
    MINIGAME_LOSS = 0     # gained from losing a minigame
    WAR_FIRST     = 10000 # given for winning a war
    WAR_SECOND    = 5000  # given for being runner-up in a war

    SKILL_COST    = 1000 # cost to reroll a waifu's skills
    WISHLIST_COST = 5000 # cost to add a waifu to wishlist

    WAIFU_PRICE   = 100

    COMMON_TRAIT_PRICE = 100
    UNCOMMON_TRAIT_PRICE = 250
    RARE_TRAIT_PRICE = 500
    LEGENDARY_TRAIT_PRICE = 1000

class Cooldowns(Enum):
    CLAIM    = 0
    DUEL     = 1
    MINIGAME = 2

class WaifuState(Enum):
    ACTIVE   = 0
    COOLDOWN = 1
    INACTIVE = 2
    SOLD     = 3
    NULL     = 4

class Weekday(Enum):
    MONDAY    = 1
    TUESDAY   = 2
    WEDNESDAY = 3
    THURSDAY  = 4
    FRIDAY    = 5
    SATURDAY  = 6
    SUNDAY    = 7

    @classmethod
    def today(cls):
        print("today is %s" % cls(datetime.date.today().isoweekday()).name)
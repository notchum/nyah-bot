import datetime
from enum import Enum

import disnake

class Emojis:
    CHECK_MARK = "✔️"
    CROSS_MARK = "✖️"

    RED_BOX  = "🟥"
    BLUE_BOX = "🟦"

    TICKET     = "<:nyah_ticket:1306531129016188979>"
    COINS      = "<:coins:1158472639413764178>"
    SWAP       = "<:replace:1158888082343477258>"
    PREV_PAGE  = "<:leftWaifu:1158460793063477420>"
    NEXT_PAGE  = "<:rightWaifu:1158460837359538186>"
    FIRST_PAGE = "<a:remspin:1159723782047551510>"
    LAST_PAGE  = "<a:ramspin:1159723691698044968>"
    
    CLAIM    = "<a:_:1167319600472531015>"
    MINIGAME = "🎮"
    DUEL     = "🎌"

    ITEM_CHEST_KEY    = "🗝️"
    ITEM_TRAIT_SCROLL = "📜"
    ITEM_SHONEN_STONE = "💎"
    ITEM_HEALTH_TEA   = "🍵"

    SKILL_ATTACK  = "🗡️"
    SKILL_DEFENSE = "🛡️"
    SKILL_HEALTH  = "❤️"
    SKILL_SPEED   = "🌀"
    SKILL_MAGIC   = "✨"
    SKILL_TOTAL   = "🎯"

    TRAIT_STAR = "🌟"

    SHOPPING_CART = "🛒"

    TIER_BRONZE  = "<:tier_bronze:1274833983812669511>"
    TIER_SILVER  = "<:tier_silver:1274833982273618002>"
    TIER_GOLD    = "<:tier_gold:1274833981250207907>"
    TIER_EMERALD = "<:tier_emerald:1274833976120578139>"
    TIER_RUBY    = "<:tier_ruby:1274833978544750743>"
    TIER_DIAMOND = "<:tier_diamond:1274833976925622387>"

    STATE_MARRIED   = "💕"
    STATE_COOLDOWN  = "❄️"
    STATE_UNMARRIED = "💔"

class ItemTypes(Enum):
    ITEM_CHEST_KEY    = 1
    ITEM_TRAIT_SCROLL = 2
    ITEM_SHONEN_STONE = 3
    ITEM_HEALTH_TEA   = 4

class Experience(Enum):
    BASE_LEVEL   = 100 # base amount of XP per level
    CLAIM        = 5   # gained from claiming a character
    DUEL_WIN     = 15  # gained from winning a duel
    MINIGAME_WIN = 5   # gained from beating a minigame
    WAR_ROUND    = 25  # gained from each round of a war
    WAR_FIRST    = 75  # gained from winning a war
    WAR_SECOND   = 50  # gained from being runner-up in a war

class Prices(Enum):
    COST_ITEM_CHEST_KEY    = 100
    COST_ITEM_TRAIT_SCROLL = 100
    COST_ITEM_SHONEN_STONE = 100
    COST_ITEM_HEALTH_TEA   = 10

    COST_CHARACTER_BRONZE  = 3
    COST_CHARACTER_SILVER  = 12
    COST_CHARACTER_GOLD    = 45
    COST_CHARACTER_EMERALD = 160
    COST_CHARACTER_RUBY    = 600
    COST_CHARACTER_DIAMOND = 2250

    PAYOUT_CHARACTER_BRONZE  = 1
    PAYOUT_CHARACTER_SILVER  = 4
    PAYOUT_CHARACTER_GOLD    = 15
    PAYOUT_CHARACTER_EMERALD = 55
    PAYOUT_CHARACTER_RUBY    = 200
    PAYOUT_CHARACTER_DIAMOND = 750

    PAYOUT_LEVEL_UP          = 50
    PAYOUT_MINIGAME_WIN      = 2
    PAYOUT_WAR_FIRST         = 500
    PAYOUT_WAR_SECOND        = 250
    PAYOUT_WAR_PARTICIPATE   = 125

class Cooldowns(Enum):
    CLAIM    = 0
    DUEL     = 1
    MINIGAME = 2

class Tiers(Enum):
    BRONZE  = 1
    SILVER  = 2
    GOLD    = 3
    EMERALD = 4
    RUBY    = 5
    DIAMOND = 6

class Fusions(Enum):
    SILVER  = 1
    GOLD    = 2
    EMERALD = 3
    RUBY    = 4
    DIAMOND = 5

class WaifuState(Enum):
    NULL     = None
    ACTIVE   = 1
    COOLDOWN = 2
    INACTIVE = 3
    SOLD     = 4
    FUSED    = 5

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

TIER_PERCENTILE_MAP = {
    Tiers.DIAMOND: (99, 100),
    Tiers.RUBY: (95, 99),
    Tiers.EMERALD: (85, 95),
    Tiers.GOLD: (70, 85),
    Tiers.SILVER: (50, 70),
    Tiers.BRONZE: (0, 50),
}

TIER_COLOR_MAP = {
    Tiers.BRONZE: disnake.Color.from_rgb(110, 67, 32),
    Tiers.SILVER: disnake.Color.from_rgb(192, 192, 192),
    Tiers.GOLD: disnake.Color.gold(),
    Tiers.EMERALD: disnake.Color.from_rgb(68, 204, 87),
    Tiers.RUBY: disnake.Color.from_rgb(207, 35, 35),
    Tiers.DIAMOND: disnake.Color.teal(),
}

TIER_TITLE_MAP = {
    Tiers.BRONZE: f"{Emojis.TIER_BRONZE} Bronze",
    Tiers.SILVER: f"{Emojis.TIER_SILVER} Silver",
    Tiers.GOLD: f"{Emojis.TIER_GOLD} Gold",
    Tiers.EMERALD: f"{Emojis.TIER_EMERALD} Emerald",
    Tiers.RUBY: f"{Emojis.TIER_RUBY} Ruby",
    Tiers.DIAMOND: f"{Emojis.TIER_DIAMOND} Diamond",
}

TIER_EMOJI_MAP = {
    Tiers.BRONZE: Emojis.TIER_BRONZE,
    Tiers.SILVER: Emojis.TIER_SILVER,
    Tiers.GOLD: Emojis.TIER_GOLD,
    Tiers.EMERALD: Emojis.TIER_EMERALD,
    Tiers.RUBY: Emojis.TIER_RUBY,
    Tiers.DIAMOND: Emojis.TIER_DIAMOND,
}

TIER_COST_MAP = {
    Tiers.BRONZE: Prices.COST_CHARACTER_BRONZE,
    Tiers.SILVER: Prices.COST_CHARACTER_SILVER,
    Tiers.GOLD: Prices.COST_CHARACTER_GOLD,
    Tiers.EMERALD: Prices.COST_CHARACTER_EMERALD,
    Tiers.RUBY: Prices.COST_CHARACTER_RUBY,
    Tiers.DIAMOND: Prices.COST_CHARACTER_DIAMOND,
}

TIER_PAYOUT_MAP = {
    Tiers.BRONZE: Prices.PAYOUT_CHARACTER_BRONZE,
    Tiers.SILVER: Prices.PAYOUT_CHARACTER_SILVER,
    Tiers.GOLD: Prices.PAYOUT_CHARACTER_GOLD,
    Tiers.EMERALD: Prices.PAYOUT_CHARACTER_EMERALD,
    Tiers.RUBY: Prices.PAYOUT_CHARACTER_RUBY,
    Tiers.DIAMOND: Prices.PAYOUT_CHARACTER_DIAMOND,
}

FUSION_TIER_MAP = {
    Fusions.SILVER: Tiers.SILVER,
    Fusions.GOLD: Tiers.GOLD,
    Fusions.EMERALD: Tiers.EMERALD,
    Fusions.RUBY: Tiers.RUBY,
    Fusions.DIAMOND: Tiers.DIAMOND,
}

WAIFUSTATE_TITLE_MAP = {
    WaifuState.ACTIVE: f"{Emojis.STATE_MARRIED} Married",
    WaifuState.COOLDOWN: f"{Emojis.STATE_COOLDOWN} Cooldown",
    WaifuState.INACTIVE: f"{Emojis.STATE_UNMARRIED} Unmarried",
}

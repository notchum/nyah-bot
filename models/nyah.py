import datetime
from typing import Optional, List
from uuid import UUID, uuid4

import disnake
from pydantic import Field
from beanie import Document

from models import Claim
from nyahbot.util import utilities
from nyahbot.util.constants import (
    Emojis,
    WaifuState,
    Experience,
    Money,
    Cooldowns,
)

cooldown_attribute_map = {
    Cooldowns.CLAIM: {
        "interval": "interval_claim_mins",
        "timestamp": "timestamp_last_claim",
    },
    Cooldowns.DUEL: {
        "interval": "interval_duel_mins",
        "timestamp": "timestamp_last_duel",
    },
    Cooldowns.MINIGAME: {
        "interval": "interval_minigame_mins",
        "timestamp": "timestamp_last_minigame",
    },
}

def calculate_xp_for_level(level: int) -> int:
    """ Returns the XP needed for this level before the next. """
    if level == 1:
        return Experience.BASE_LEVEL.value
    else:
        previous_xp = calculate_xp_for_level(level - 1)
        return int(previous_xp + int(previous_xp * 0.05))

def calculate_accumulated_xp(level: int) -> int:
    """ Returns the total XP needed to reach this level. """
    xp_accumulated = 0
    for level in range(1, level + 1):
        xp_needed = calculate_xp_for_level(level)
        xp_accumulated += xp_needed
    return xp_accumulated

class NyahPlayer(Document):
    class Settings:
        name = "players"
        indexes = [
            "user_id",
        ]
    
    id: UUID = Field(default_factory=uuid4)
    user_id: int
    name: str
    
    score: int
    money: int
    xp: int
    level: int
    
    wishlist: List[str]
    
    timestamp_last_duel: Optional[datetime.datetime] = None
    timestamp_last_claim: Optional[datetime.datetime] = None
    timestamp_last_minigame: Optional[datetime.datetime] = None

    async def add_user_xp(self, user: disnake.Member | disnake.User, xp: int, channel: disnake.TextChannel = None) -> None:
        self.xp += xp
        # logger.info(f"{user.name}[{user.id}] gained {xp}XP ({self.xp}XP)")

        # check if they leveled up
        if self.xp > calculate_accumulated_xp(self.level + 1):
            self.level += 1
            level_money = Money.PER_LEVEL.value * self.level
            self.money += level_money
            if channel:
                level_up_embed = disnake.Embed(
                    description=f"### ㊗️ Congratulations {user.mention}! You are now level {self.level}!\n\n"
                                f"You have been awarded `{level_money:,}` {Emojis.COINS}",
                    color=disnake.Color.dark_teal()
                ).set_thumbnail(url=user.avatar.url)
                await channel.send(embed=level_up_embed)
            # logger.info(f"{user.name}[{user.id}] leveled up to level {self.level}")
        
        await self.save()

    async def add_user_mmr(self, mmr: int) -> None:
        if self.score + mmr <= 0:
            self.score = 0
        else:
            self.score += mmr
        await self.save()

    async def add_user_money(self, money: int) -> None:
        if self.money + money <= 0:
            self.money = 0
        else:
            self.money += money
        await self.save()

    async def sell_waifu(self, claim: Claim) -> None:
        claim.state = WaifuState.SOLD.name
        claim.index = None
        await claim.save()
        await self.add_user_money(claim.price)

    async def user_is_on_cooldown(self, cooldown_type: Cooldowns) -> bool:
        nyah_config = await utilities.fetch_nyah_config()
        interval: int = getattr(nyah_config, cooldown_attribute_map[cooldown_type]["interval"])
        timestamp: datetime.datetime = getattr(self, cooldown_attribute_map[cooldown_type]["timestamp"])

        if timestamp == None:
            return False # user not on cooldown
        
        timedelta = disnake.utils.utcnow() - timestamp
        if timedelta > datetime.timedelta(minutes=interval):
            return False # user not on cooldown
        
        return True # user is on cooldown

    async def user_cooldown_expiration_time(self, cooldown_type: Cooldowns) -> datetime.datetime:
        nyah_config = await utilities.fetch_nyah_config()
        interval: int = getattr(nyah_config, cooldown_attribute_map[cooldown_type]["interval"])
        timestamp: datetime.datetime = getattr(self, cooldown_attribute_map[cooldown_type]["timestamp"])

        return timestamp + datetime.timedelta(minutes=interval)

    async def reset_cooldown(self, cooldown_type: str) -> None:
        setattr(self, cooldown_attribute_map[cooldown_type]["timestamp"], None)
        await self.save()

    async def reindex_guild_user_harem(guild: disnake.Guild, user: disnake.User | disnake.Member) -> None:
        nyah_config = await utilities.fetch_nyah_config()

        # Get user's harem
        harem = await reql_helpers.get_harem(guild, user)

        # Figure out how many waifus are ACTIVE and INACTIVE
        active_count = sum(1 for claim in harem if claim.state == WaifuState.ACTIVE.name)
        inactive_count = sum(1 for claim in harem if claim.state == WaifuState.INACTIVE.name)

        # Ensure there are at most 3 ACTIVE claims and at least 0 INACTIVE claims
        if active_count < nyah_config.waifu_max_marriages and inactive_count > 0:
            for claim in harem:
                if claim.state == WaifuState.INACTIVE.name:
                    claim.state = WaifuState.ACTIVE.name
                    active_count += 1
                if active_count >= nyah_config.waifu_max_marriages:
                    break
        elif active_count > nyah_config.waifu_max_marriages:
            for claim in harem:
                if claim.state == WaifuState.ACTIVE.name:
                    claim.state = WaifuState.INACTIVE.name
                    active_count -= 1
                if active_count <= nyah_config.waifu_max_marriages:
                    break
        
        # Sort by state and index
        sorted_harem = sorted(harem, key=lambda claim: (WaifuState[claim.state].value, claim.index))

        # Re-index
        for i, claim in enumerate(sorted_harem):
            claim.index = i
            
            # Update the claim in the db
            await reql_helpers.set_waifu_claim(claim)
        
        logger.info(f"{guild.name}[{guild.id}] | "
                    f"{user.name}[{user.id}] | "
                    f"Reindexed user's harem")


class NyahConfig(Document):
    class Settings:
        name = "config"
    
    id: UUID = Field(default_factory=uuid4)

    waifu_war_hour: int
    waifu_max_marriages: int
    
    interval_claim_mins: int
    interval_duel_mins: int
    interval_minigame_mins: int
    interval_season_days: int
    
    timestamp_last_season_end: Optional[datetime.datetime] = None


class NyahGuild(Document):
    class Settings:
        name = "guilds"
        indexes = [
            "guild_id",
        ]
    
    id: UUID = Field(default_factory=uuid4)
    guild_id: int
    name: str
    waifu_war_channel_id: int

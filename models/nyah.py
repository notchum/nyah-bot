import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

import disnake
from pydantic import Field
from beanie import Document

from models import Claim
from utils import Emojis, WaifuState, Cooldowns, Money
import utils.utilities as utils

logger = logging.getLogger("nyahbot")
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


class NyahConfig(Document):
    class Settings:
        name = "config"
        bson_encoders = {
            datetime: str
        }
    
    id: UUID = Field(default_factory=uuid4)

    waifu_war_hour: int
    waifu_max_marriages: int
    
    interval_claim_mins: int
    interval_duel_mins: int
    interval_minigame_mins: int
    interval_season_days: int
    
    timestamp_last_season_end: datetime

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


class NyahPlayer(Document):
    class Settings:
        name = "players"
        indexes = [
            "user_id",
        ]
        bson_encoders = {
            datetime: str
        }
    
    id: UUID = Field(default_factory=uuid4)
    user_id: int
    name: str
    
    score: int
    money: int
    xp: int
    level: int
    
    wishlist: List[str]
    
    timestamp_last_duel: Optional[datetime] = None
    timestamp_last_claim: Optional[datetime] = None
    timestamp_last_minigame: Optional[datetime] = None

    async def add_user_xp(self, xp: int, user: disnake.Member | disnake.User = None, channel: disnake.TextChannel = None) -> None:
        self.xp += xp

        # check if they leveled up
        if self.xp >= utils.calculate_accumulated_xp(self.level + 1):
            self.level += 1
            level_money = Money.PER_LEVEL.value * self.level
            self.money += level_money
            if channel and user:
                level_up_embed = disnake.Embed(
                    description=f"### ㊗️ Congratulations {user.mention}! You are now level {self.level}!\n\n"
                                f"You have been awarded `{level_money:,}` {Emojis.COINS}",
                    color=disnake.Color.dark_teal()
                ).set_thumbnail(url=user.avatar.url)
                await channel.send(embed=level_up_embed)
        
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
        result = await NyahConfig.find().limit(1).to_list() # using query instead of fetch_nyah_config() to avoid circular import
        nyah_config = result[0]
        
        interval: int = getattr(nyah_config, cooldown_attribute_map[cooldown_type]["interval"])
        timestamp: datetime = getattr(self, cooldown_attribute_map[cooldown_type]["timestamp"])

        if timestamp == None:
            return False # user not on cooldown
        
        tdelta = disnake.utils.utcnow() - timestamp
        if tdelta > timedelta(minutes=interval):
            return False # user not on cooldown
        
        return True # user is on cooldown

    async def user_cooldown_expiration_time(self, cooldown_type: Cooldowns) -> datetime:
        result = await NyahConfig.find().limit(1).to_list() # using query instead of fetch_nyah_config() to avoid circular import
        nyah_config = result[0]

        interval: int = getattr(nyah_config, cooldown_attribute_map[cooldown_type]["interval"])
        timestamp: datetime = getattr(self, cooldown_attribute_map[cooldown_type]["timestamp"])

        return timestamp + timedelta(minutes=interval)

    async def reset_cooldown(self, cooldown_type: Cooldowns) -> None:
        setattr(self, cooldown_attribute_map[cooldown_type]["timestamp"], None)
        await self.save()

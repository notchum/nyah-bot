from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

import disnake
import pymongo
from pydantic import BaseModel, Field
from beanie import init_beanie, Document

from nyahbot.util.constants import Emojis

##*************************************************##
##********            WAIFUS DB             *******##
##*************************************************##

class Waifu(Document):
    class Settings:
        name = "core"
        indexes = [
            "slug",
        ]
    
    # id: UUID = Field(default_factory=uuid4)
    slug: str
    url: str
    source: str

    name: str
    original_name: Optional[str] = None
    romaji_name: Optional[str] = None
    
    husbando: bool
    description: Optional[str] = None
    image_url: str
    series: List[str]
    origin: Optional[str] = None

    height: Optional[str] = None
    weight: Optional[str] = None
    blood_type: Optional[str] = None

    bust: Optional[str] = None
    waist: Optional[str] = None
    hip: Optional[str] = None

    age: Optional[str] = None
    date_of_birth: Optional[str] = None
    birthday_day: Optional[int] = None
    birthday_month: Optional[int] = None
    birthday_year: Optional[int] = None

    popularity_rank: Optional[int] = None
    like_rank: Optional[int] = None
    trash_rank: Optional[int] = None

    tags: List[str]

class Claim(Document):
    class Settings:
        name = "claims"
        indexes = [
            "slug",
            "user_id",
            "guild_id",
        ]
    
    id: UUID = Field(default_factory=uuid4)
    slug: str

    guild_id: int
    channel_id: int
    message_id: int
    user_id: int

    jump_url: str
    image_url: str
    cached_images_urls: List[str]

    state: Optional[str] = None
    index: Optional[int] = None
    price: int

    attack: int
    defense: int
    health: int
    speed: int
    magic: int

    attack_mod: Optional[int] = 0
    defense_mod: Optional[int] = 0
    health_mod: Optional[int] = 0
    speed_mod: Optional[int] = 0
    magic_mod: Optional[int] = 0

    trait_common: Optional[str] = None
    trait_uncommon: Optional[str] = None
    trait_rare: Optional[str] = None
    trait_legendary: Optional[str] = None

    timestamp: datetime
    timestamp_cooldown: Optional[datetime] = None

    # def calculate_base_stats(self) -> int:
    #     return self.attack + self.defense + self.health + self.speed + self.magic
    
    # def calculate_mod_stats(self) -> int:
    #     return self.attack_mod + self.defense_mod + self.health_mod + self.speed_mod + self.magic_mod
    
    # def calculate_total_stats(self) -> int:
    #     return self.calculate_base_stats() + self.calculate_mod_stats()
    
    # def stats_str(self) -> str:
    #     mod_stats = self.calculate_mod_stats()
    #     operator = "+" if mod_stats >= 0 else ""
    #     return f"{self.calculate_base_stats()}{operator}{mod_stats} SP"
    
    # def price_str(self) -> str:
    #     return f"`{self.price:,}` {Emojis.COINS}"

    # def skill_str(self) -> str:
    #     return f"🗡️`Attack  {self.attack: >5}{'+' if self.attack_mod >= 0 else ''}{self.attack_mod}`\n" \
    #            f"🛡️`Defense {self.defense: >5}{'+' if self.defense_mod >= 0 else ''}{self.defense_mod}`\n" \
    #            f"❤️`Health  {self.health: >5}{'+' if self.health_mod >= 0 else ''}{self.health_mod}`\n" \
    #            f"🌀`Speed   {self.speed: >5}{'+' if self.speed_mod >= 0 else ''}{self.speed_mod}`\n" \
    #            f"✨`Magic   {self.magic: >5}{'+' if self.magic_mod >= 0 else ''}{self.magic_mod}`\n"
    
    # def trait_str(self) -> str:
    #     trait_str = ""
    
    #     if self.trait_common:
    #         trait_str += f"🟢`{self.trait_common}`\n"
    #     if self.trait_uncommon:
    #         trait_str += f"🔵`{self.trait_uncommon}`\n"
    #     if self.trait_rare:
    #         trait_str += f"🟣`{self.trait_rare}`\n"
    #     if self.trait_legendary:
    #         trait_str += f"🟠`{self.trait_legendary}`\n"
        
    #     return trait_str if trait_str else "None"

##*************************************************##
##********             NYAH DB              *******##
##*************************************************##

class NyahPlayer(Document):
    class Settings:
        name = "players"
        indexes = [
            "user_id",
        ]
    
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

class NyahGuild(Document):
    class Settings:
        name = "guilds"
        indexes = [
            "guild_id",
        ]
    
    guild_id: int
    name: str

    waifu_war_channel_id: int
    waifu_war_hour: int
    waifu_max_marriages: int
    
    interval_claim_mins: int
    interval_duel_mins: int
    interval_minigame_mins: int
    interval_season_days: int
    
    timestamp_last_season_end: Optional[datetime] = None

##*************************************************##
##********             WARS DB              *******##
##*************************************************##

class Vote(Document):
    class Settings:
        name = "votes"

    id: UUID = Field(default_factory=uuid4)
    battle_id: UUID = Field(default_factory=uuid4)
    waifu_vote_id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    user_id: int
    # other
    timestamp: datetime

class Battle(Document):
    class Settings:
        name = "battles"

    id: UUID = Field(default_factory=uuid4)
    match_id: UUID = Field(default_factory=uuid4)
    waifu_red_id: UUID = Field(default_factory=uuid4)
    waifu_blue_id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    message_id: Optional[int] = None
    # other
    number: int
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None

class Match(Document):
    class Settings:
        name = "matches"
    
    id: UUID = Field(default_factory=uuid4)
    round_id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    user_red_id: int
    user_blue_id: int
    winner_id: Optional[int] = None
    # other
    number: int
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None

class Round(Document):
    class Settings:
        name = "rounds"
    
    id: UUID = Field(default_factory=uuid4)
    war_id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    message_id: Optional[int] = None
    # other
    number: int
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None

class War(Document):
    class Settings:
        name = "core"
    
    id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    event_id: int
    guild_id: int
    # other
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None

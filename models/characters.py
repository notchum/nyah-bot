from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import Field
from beanie import Document

from utils import Emojis, WaifuState

class Waifu(Document):
    class Settings:
        name = "core"
        indexes = [
            "slug",
        ]
    
    id: UUID = Field(default_factory=uuid4)
    slug: str
    url: str
    source: str

    name: str
    original_name: Optional[str] = None
    romaji_name: Optional[str] = None
    
    husbando: bool
    description: str
    image_url: str
    series: List[str]
    origin: Optional[str] = None

    height: Optional[str] = None
    weight: Optional[str] = None
    blood_type: Optional[str] = None

    bust: Optional[str] = None
    waist: Optional[str] = None
    hip: Optional[str] = None

    age: Optional[int] = None
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
        bson_encoders = {
            datetime: str
        }
    
    id: UUID = Field(default_factory=uuid4)
    slug: str

    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    message_id: Optional[int] = None
    user_id: int

    jump_url: Optional[str] = None
    image_url: str
    cached_images_urls: List[str]

    state: Optional[int] = None # WaifuState
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

    timestamp: Optional[datetime] = None
    timestamp_cooldown: Optional[datetime] = None

    def marry(self) -> None:
        self.state = WaifuState.ACTIVE.name

    @property
    def base_stats(self) -> int:
        return self.attack + self.defense + self.health + self.speed + self.magic
    
    @property
    def mod_stats(self) -> int:
        return self.attack_mod + self.defense_mod + self.health_mod + self.speed_mod + self.magic_mod
    
    @property
    def total_stats(self) -> int:
        return self.base_stats + self.mod_stats
    
    @property
    def stats_str(self) -> str:
        mod_stats = self.mod_stats
        operator = "+" if mod_stats >= 0 else ""
        return f"{self.base_stats}{operator}{mod_stats} SP"
    
    @property
    def price_str(self) -> str:
        return f"`{self.price:,}` {Emojis.COINS}"

    @property
    def skill_str(self) -> str:
        return f"🗡️`Attack  {self.attack: >5}{'+' if self.attack_mod >= 0 else ''}{self.attack_mod}`\n" \
               f"🛡️`Defense {self.defense: >5}{'+' if self.defense_mod >= 0 else ''}{self.defense_mod}`\n" \
               f"❤️`Health  {self.health: >5}{'+' if self.health_mod >= 0 else ''}{self.health_mod}`\n" \
               f"🌀`Speed   {self.speed: >5}{'+' if self.speed_mod >= 0 else ''}{self.speed_mod}`\n" \
               f"✨`Magic   {self.magic: >5}{'+' if self.magic_mod >= 0 else ''}{self.magic_mod}`\n"
    
    @property
    def trait_str(self) -> str:
        trait_str = ""
        if self.trait_common:
            trait_str += f"🟢`{self.trait_common}`\n"
        if self.trait_uncommon:
            trait_str += f"🔵`{self.trait_uncommon}`\n"
        if self.trait_rare:
            trait_str += f"🟣`{self.trait_rare}`\n"
        if self.trait_legendary:
            trait_str += f"🟠`{self.trait_legendary}`\n"
        return trait_str if trait_str else "None"


class Harem(List[Claim]):
    def __init__(self, claims: List[Claim]) -> None:
        super().__init__(claims)
    
    async def reindex(self) -> None:
        # Figure out how many waifus are ACTIVE and INACTIVE
        # active_count = sum(1 for claim in self if claim.state == WaifuState.ACTIVE.name)
        # inactive_count = sum(1 for claim in self if claim.state == WaifuState.INACTIVE.name)

        # Ensure there are at most 3 ACTIVE claims and at least 0 INACTIVE claims
        # if active_count < nyah_config.waifu_max_marriages and inactive_count > 0:
        #     for claim in self:
        #         if claim.state == WaifuState.INACTIVE.name:
        #             claim.state = WaifuState.ACTIVE.name
        #             active_count += 1
        #         if active_count >= nyah_config.waifu_max_marriages:
        #             break
        # elif active_count > nyah_config.waifu_max_marriages:
        #     for claim in self:
        #         if claim.state == WaifuState.ACTIVE.name:
        #             claim.state = WaifuState.INACTIVE.name
        #             active_count -= 1
        #         if active_count <= nyah_config.waifu_max_marriages:
        #             break
        
        # Sort by state and index
        self = sorted(self, key=lambda claim: (WaifuState[claim.state].value, claim.index))

        # Re-index
        for index, claim in enumerate(self):
            claim.index = index
            await claim.save()

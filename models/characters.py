import random
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from importlib import import_module

from pydantic import Field
from beanie import Document
from beanie.operators import Set
from beanie.odm.bulk import BulkWriter

from utils.traits import TraitTypes
from utils.constants import Emojis, WaifuState, Tiers, TIER_PAYOUT_MAP

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
    name: str

    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    message_id: Optional[int] = None
    user_id: int

    jump_url: Optional[str] = None
    image_url: str
    cached_images_urls: Optional[List[str]] = []

    state: WaifuState = Field(None)
    index: Optional[int] = None
    tier: Tiers = Field()

    attack: Optional[int] = None
    health: Optional[int] = None
    speed: Optional[int] = None

    trait: TraitTypes = Field(TraitTypes.NONE) # TODO, keep storing the same but on object creation just create the `Trait` object

    health_points: Optional[int] = None

    timestamp: Optional[datetime] = None
    timestamp_cooldown: Optional[datetime] = None

    def marry(self) -> None:
        self.state = WaifuState.ACTIVE
    
    def divorce(self) -> None:
        self.state = WaifuState.INACTIVE
    
    def cooldown(self) -> None:
        self.state = WaifuState.COOLDOWN
    
    def roll_skills(self) -> None:
        self.attack = random.choice(range(10, 101, 10)) # 10 - 100, step 10
        self.health = random.choice(range(50, 251, 10)) # 50 - 250, step 10
        self.speed = random.choice(range(10, 101, 10)) # 10 - 100, step 10
    
    def roll_trait(self) -> None:
        self.trait = random.choice([t for t in list(TraitTypes) if t != TraitTypes.NONE])
    
    def add_hp(self, amount: int) -> None:
        self.health_points += amount

    def reset_hp(self) -> None:
        self.health_points = self.health

    @property
    def is_married(self) -> bool:
        return self.state == WaifuState.ACTIVE

    @property
    def total_skill_points(self) -> int:
        return self.attack + self.health + self.speed
    
    @property
    def skill_str_short(self) -> str:
        return f"{Emojis.SKILL_TOTAL} {(self.total_skill_points / 450) * 100:.1f}%"

    @property
    def skill_str_long(self) -> str:
        return f"{Emojis.SKILL_ATTACK}`Attack  {self.attack: >5}`\n" \
               f"{Emojis.SKILL_HEALTH}`Health  {self.health: >5}`\n" \
               f"{Emojis.SKILL_SPEED}`Speed   {self.speed: >5}`\n" \

    @property
    def price_str(self) -> str:
        return f"`{TIER_PAYOUT_MAP[self.tier].value:,}` {Emojis.COINS}"
    
    @property
    def trait_str(self) -> str:
        if self.trait:
            return f"{Emojis.TRAIT_STAR}`{self.trait.name.replace('_', ' ').title()}`\n"
        else:
            return "None"
    
    @property
    def health_bar_str(self) -> str:
        segments = 10
        self.health_points = max(0, min(self.health_points, self.health))
        health_percent = self.health_points / self.health
        filled = round(health_percent * segments)
        empty = segments - filled
        health_bar = "❤️" * filled + "🖤" * empty
        return f"{health_bar} [{self.health_points}/{self.health}]"


class Harem(List[Claim]):
    def __init__(self, claims: List[Claim]) -> None:
        super().__init__(claims)
    
    async def reindex(self) -> None:
        async with BulkWriter() as bulk_writer:
            for index, claim in enumerate(self, 1):
                if claim.index != index:
                    await Claim.find_one(
                        Claim.id == claim.id
                    ).update_one(
                        Set({Claim.index: index}), bulk_writer=bulk_writer
                    )

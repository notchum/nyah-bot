import random
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from importlib import import_module

from pydantic import Field
from beanie import Document

from utils import Emojis, WaifuState, Money
import utils.traits as traits

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

    trait_common: Optional[int] = None
    trait_uncommon: Optional[int] = None
    trait_rare: Optional[int] = None
    trait_legendary: Optional[int] = None

    timestamp: Optional[datetime] = None
    timestamp_cooldown: Optional[datetime] = None

    def marry(self) -> None:
        self.state = WaifuState.ACTIVE.value
    
    def divorce(self) -> None:
        self.state = WaifuState.INACTIVE.value
    
    def cooldown(self) -> None:
        self.state = WaifuState.COOLDOWN.value
    
    async def roll_skills(self) -> None:
        NyahPlayer = import_module("models").NyahPlayer
        player = await NyahPlayer.find_one(NyahPlayer.user_id == self.user_id) # using query instead of fetch_nyah_player() to avoid circular import
        
        random_stat = lambda l: random.randint(0, max(random.randint(1, 10), min(100, l * 10)))
        self.attack = random_stat(player.level)
        self.defense = random_stat(player.level)
        self.health = random_stat(player.level)
        self.speed = random_stat(player.level)
        self.magic = random_stat(player.level)
    
    async def roll_traits(self) -> None:
        NyahPlayer = import_module("models").NyahPlayer
        player = await NyahPlayer.find_one(NyahPlayer.user_id == self.user_id) # using query instead of fetch_nyah_player() to avoid circular import
        
        trait_dropper = traits.CharacterTraitDropper(player.level)
        trait_common = trait_dropper.drop_common_trait()
        trait_uncommon = trait_dropper.drop_uncommon_trait()
        trait_rare = trait_dropper.drop_rare_trait()
        trait_legendary = trait_dropper.drop_legendary_trait()

        self.trait_common = trait_common.trait_number
        self.trait_uncommon = trait_uncommon.trait_number
        self.trait_rare = trait_rare.trait_number
        self.trait_legendary = trait_legendary.trait_number

        if self.trait_common: trait_common.apply_modifiers(self)
        if self.trait_uncommon: trait_uncommon.apply_modifiers(self)
        if self.trait_rare: trait_rare.apply_modifiers(self)
        if self.trait_legendary: trait_legendary.apply_modifiers(self)
    
    async def calculate_price(self) -> None:
        # Normalize each ranking, adding some various permutations to a list
        # num_ranks = await self.bot.mongo.fetch_waifu_count()
        # normalized_popularity_rank = 1 - (new_waifu.popularity_rank - 1) / (num_ranks - 1)
        # normalized_like_rank = 1 - (new_waifu.like_rank - 1) / (num_ranks - 1)
        # normalized_trash_rank = (new_waifu.trash_rank - 1) / (num_ranks - 1)
        # base_normalizations = [
        #     normalized_like_rank - normalized_trash_rank,
        #     normalized_popularity_rank - normalized_trash_rank,
        #     normalized_popularity_rank + normalized_like_rank - normalized_trash_rank,
        # ]

        # Calculate base stats
        # attack = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        # defense = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        # health = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        # speed = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        # magic = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        
        # Calculate price
        # normalized_total_stats = ((attack + defense + health + speed + magic) / 500)
        # popularity_price = int(round(normalized_popularity_rank * 1000))
        # stats_price = int(round(0.2 * normalized_total_stats * 100))
        # traits_price = sum([t.money_value for t in rolled_traits.values() if t != None])
        # price = max(100, popularity_price + stats_price + traits_price)

        # using queries here to avoid circular import
        num_ranks = await Waifu.count()
        waifu = await Waifu.find_one(Waifu.slug == self.slug)

        # calculate popularity price
        if waifu.popularity_rank <= 0.05 * num_ranks:  # Top 5%
            dividend = 10
        elif waifu.popularity_rank <= 0.2 * num_ranks:  # Top 20%
            dividend = 15
        elif waifu.popularity_rank <= 0.4 * num_ranks:  # Top 40%
            dividend = 22
        elif waifu.popularity_rank <= 0.6 * num_ranks:  # Top 60%
            dividend = 32
        elif waifu.popularity_rank <= 0.8 * num_ranks:  # Top 80%
            dividend = 43
        else:  # Bottom 20%
            dividend = 55
        popularity_price = max(Money.WAIFU_PRICE.value, (num_ranks - waifu.popularity_rank - 1) // dividend)

        # calculate traits price
        traits_price = 0
        if self.trait_common:
            traits_price = traits.get_trait(traits.TraitTypes.COMMON, self.trait_common).money_value
        if self.trait_uncommon:
            traits_price = traits.get_trait(traits.TraitTypes.UNCOMMON, self.trait_uncommon).money_value
        if self.trait_rare:
            traits_price = traits.get_trait(traits.TraitTypes.RARE, self.trait_rare).money_value
        if self.trait_legendary:
            traits_price = traits.get_trait(traits.TraitTypes.LEGENDARY, self.trait_legendary).money_value
        
        # calculate stats negative price
        stats_price = 500 - self.base_stats 

        # calculate total price
        self.price = max(Money.WAIFU_PRICE.value, (popularity_price + traits_price - stats_price))

    @property
    def is_married(self) -> bool:
        return self.state == WaifuState.ACTIVE.value

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
        return f"{Emojis.SKILL_ATTACK}`Attack  {self.attack: >5}{'+' if self.attack_mod >= 0 else ''}{self.attack_mod}`\n" \
               f"{Emojis.SKILL_DEFENSE}`Defense {self.defense: >5}{'+' if self.defense_mod >= 0 else ''}{self.defense_mod}`\n" \
               f"{Emojis.SKILL_HEALTH}`Health  {self.health: >5}{'+' if self.health_mod >= 0 else ''}{self.health_mod}`\n" \
               f"{Emojis.SKILL_SPEED}`Speed   {self.speed: >5}{'+' if self.speed_mod >= 0 else ''}{self.speed_mod}`\n" \
               f"{Emojis.SKILL_MAGIC}`Magic   {self.magic: >5}{'+' if self.magic_mod >= 0 else ''}{self.magic_mod}`\n"
    
    @property
    def trait_str(self) -> str:
        trait_str = ""
        if self.trait_common:
            trait_str += f"{Emojis.TRAIT_COMMON}`{traits.get_trait(traits.TraitTypes.COMMON, self.trait_common).name}`\n"
        if self.trait_uncommon:
            trait_str += f"{Emojis.TRAIT_UNCOMMON}`{traits.get_trait(traits.TraitTypes.UNCOMMON, self.trait_uncommon).name}`\n"
        if self.trait_rare:
            trait_str += f"{Emojis.TRAIT_RARE}`{traits.get_trait(traits.TraitTypes.RARE, self.trait_rare).name}`\n"
        if self.trait_legendary:
            trait_str += f"{Emojis.TRAIT_LEGENDARY}`{traits.get_trait(traits.TraitTypes.LEGENDARY, self.trait_legendary).name}`\n"
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
        self = sorted(self, key=lambda claim: (claim.state, claim.index))

        # Re-index
        for index, claim in enumerate(self, 1):
            claim.index = index
            await claim.save()

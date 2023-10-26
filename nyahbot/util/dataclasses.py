import datetime
from typing import List
from dataclasses import dataclass, fields

from nyahbot.util.constants import Emojis

##*************************************************##
##********            NYAH DB              *******##
##*************************************************##

@dataclass(kw_only=True)
class NyahGuild():
    # primary index == guild_id
    guild_id: str
    # other
    name: str
    waifu_war_channel_id: str
    waifu_war_hour: int
    waifu_max_marriages: int
    interval_claim_mins: int
    interval_duel_mins: int
    interval_minigame_mins: int
    interval_season_days: int
    timestamp_last_season_end: datetime.datetime

@dataclass(kw_only=True)
class WarUser():
    # rethink uuid's
    id: str
    # compound secondary index called 'guild_user' == [guild_id, user_id]
    # simple secondary index == guild_id
    user_id: str
    guild_id: str
    # other
    name: str
    score: int
    money: int
    xp: int
    level: int
    skill_points: int
    wishlist: List[str]
    season_results: List[dict]
    timestamp_last_duel: datetime.datetime
    timestamp_last_claim: datetime.datetime
    timestamp_last_minigame: datetime.datetime

##*************************************************##
##********            WAIFUS DB             *******##
##*************************************************##

@dataclass(kw_only=True)
class Waifu():   
    url: str
    source: str

    name: str
    original_name: str
    romaji_name: str
    description: str
    image_url: str
    series: List[str]
    origin: str
    husbando: bool

    height: str
    weight: str
    blood_type: str

    bust: str
    waist: str
    hip: str

    age: str
    date_of_birth: str
    birthday_day: int
    birthday_month: int
    birthday_year: int

    popularity_rank: int
    like_rank: int
    trash_rank: int

    slug: str
    tags: List[str]

    @classmethod
    def compare(cls, old_instance, new_instance) -> dict:
        diff_dict = {}
        for field in fields(cls):
            field_name = field.name
            old_value = getattr(old_instance, field_name)
            new_value = getattr(new_instance, field_name)

            if old_value != new_value:
                diff_dict[field_name] = {"old": old_value, "new": new_value}
        
        return diff_dict

@dataclass(kw_only=True)
class Claim():
    id: str
    slug: str

    guild_id: str
    channel_id: str
    message_id: str
    user_id: str

    jump_url: str
    image_url: str
    cached_images_urls: List[str]

    state: str
    index: int
    price: int

    attack: int
    defense: int
    health: int
    speed: int
    magic: int

    attack_mod: int
    defense_mod: int
    health_mod: int
    speed_mod: int
    magic_mod: int

    trait_common: str
    trait_uncommon: str
    trait_rare: str
    trait_legendary: str

    timestamp: datetime.datetime
    timestamp_cooldown: datetime.datetime

    def calculate_base_stats(self) -> int:
        return self.attack + self.defense + self.health + self.speed + self.magic
    
    def calculate_mod_stats(self) -> int:
        return self.attack_mod + self.defense_mod + self.health_mod + self.speed_mod + self.magic_mod
    
    def calculate_total_stats(self) -> int:
        return self.calculate_base_stats() + self.calculate_mod_stats()
    
    def stats_str(self) -> str:
        mod_stats = self.calculate_mod_stats()
        operator = "+" if mod_stats >= 0 else ""
        return f"{self.calculate_base_stats()}{operator}{mod_stats} SP"
    
    def price_str(self) -> str:
        return f"`{self.price:,}` {Emojis.COINS}"

    def skill_str(self) -> str:
        return f"🗡️`Attack  {self.attack: >5}{'+' if self.attack_mod >= 0 else ''}{self.attack_mod}`\n" \
               f"🛡️`Defense {self.defense: >5}{'+' if self.defense_mod >= 0 else ''}{self.defense_mod}`\n" \
               f"❤️`Health  {self.health: >5}{'+' if self.health_mod >= 0 else ''}{self.health_mod}`\n" \
               f"🌀`Speed   {self.speed: >5}{'+' if self.speed_mod >= 0 else ''}{self.speed_mod}`\n" \
               f"✨`Magic   {self.magic: >5}{'+' if self.magic_mod >= 0 else ''}{self.magic_mod}`\n"
    
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

##*************************************************##
##********             WARS DB              *******##
##*************************************************##

@dataclass(kw_only=True)
class Vote():
    # rethink uuid's
    id: str
    battle_id: str
    waifu_vote_id: str
    # discord uuid's
    user_id: str
    # other
    timestamp: datetime.datetime

@dataclass(kw_only=True)
class Battle():
    # rethink uuid's
    id: str
    match_id: str
    waifu_red_id: str
    waifu_blue_id: str
    # discord uuid's
    message_id: str
    # other
    number: int
    timestamp_start: datetime.datetime
    timestamp_end: datetime.datetime

@dataclass(kw_only=True)
class Match():
    # rethink uuid's
    id: str
    round_id: str
    # discord uuid's
    user_red_id: str
    user_blue_id: str
    winner_id: str
    # other
    number: int
    timestamp_start: datetime.datetime
    timestamp_end: datetime.datetime

@dataclass(kw_only=True)
class Round():
    # rethink uuid's
    id: str
    war_id: str
    # discord uuid's
    message_id: str
    # other
    number: int
    timestamp_start: datetime.datetime
    timestamp_end: datetime.datetime

@dataclass(kw_only=True)
class War():
    # rethink uuid's
    id: str
    # discord uuid's
    event_id: str
    guild_id: str
    # other
    timestamp_start: datetime.datetime
    timestamp_end: datetime.datetime

import random
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

import disnake
from beanie import Document
from beanie.operators import NotIn
from pydantic import BaseModel, Field

import utils
from models import Waifu, Claim
from utils.constants import Emojis, WaifuState, Cooldowns, Money


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


class InventoryItem(BaseModel):
    type: int
    amount: int


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
    inventory: List[InventoryItem]

    last_command_name: Optional[str] = None
    last_command_channel_id: Optional[int] = None
    last_command_message_id: Optional[int] = None
    
    timestamp_last_duel: Optional[datetime] = None
    timestamp_last_claim: Optional[datetime] = None
    timestamp_last_minigame: Optional[datetime] = None

    async def generate_claim(self, waifu: Waifu) -> Claim:
        harem_size = await Claim.find_many(
            Claim.user_id == self.user_id,
            Claim.index != None,
            Claim.state != None,
            NotIn(Claim.state, [WaifuState.NULL.value, WaifuState.SOLD.value]),
        ).count() # using query instead of fetch_harem_count() to avoid circular import
        
        claim = Claim(
            slug=waifu.slug,
            guild_id=None,
            channel_id=None,
            message_id=None,
            user_id=self.user_id,
            jump_url=None,
            image_url=waifu.image_url,
            cached_images_urls=[],
            state=WaifuState.INACTIVE.value,
            index=harem_size + 1,
            price=0,
            attack=0,
            defense=0,
            health=0,
            speed=0,
            magic=0,
            attack_mod=0,
            defense_mod=0,
            health_mod=0,
            speed_mod=0,
            magic_mod=0,
            trait_common=None,
            trait_uncommon=None,
            trait_rare=None,
            trait_legendary=None,
            timestamp=None,
            timestamp_cooldown=None
        )

        await claim.roll_skills()
        await claim.roll_traits()
        await claim.calculate_price()
        
        return claim
    
    async def check_wishlist(self) -> str | None:
        rand_num = random.random()
        cumulative_chance = 0

        # Iterate through the slugs in the wishlist to determine the selected slug
        for slug in set(self.wishlist):
            # Calculate the chance for the current slug
            slug_chance = 0.05 * self.wishlist.count(slug)
            
            # Check if the random number falls within the chance range for this slug
            if rand_num >= cumulative_chance and rand_num < cumulative_chance + slug_chance:
                # Slug selected, remove it from the wishlist and return it
                self.wishlist = [item for item in self.wishlist if item != slug]
                return slug
            
            # Update the cumulative chance
            cumulative_chance += slug_chance

        # If no slug was selected
        return None

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
        if self.score + mmr <= 100:
            self.score = 100
        else:
            self.score += mmr
        await self.save()

    async def add_user_money(self, money: int) -> None:
        if self.money + money <= 0:
            self.money = 0
        else:
            self.money += money
        await self.save()
    
    async def add_inventory_item(self, item_type: int, item_amount: int) -> None:
        for i in self.inventory:
            if i.type == item_type:
                i.amount += item_amount
                break
        else:
            self.inventory.append(InventoryItem(type=item_type, amount=item_amount))

        await self.save()
    
    async def remove_inventory_item(self, item_type: int, item_amount: int) -> None:
        for i in self.inventory:
            if i.type == item_type:
                i.amount -= item_amount
                break
        else:
            raise ValueError(f"User {self.user_id} does not have item {item_type} in their inventory")

        await self.save()

    async def sell_waifu(self, claim: Claim) -> None:
        claim.state = WaifuState.SOLD.value
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

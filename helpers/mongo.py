import uuid
from typing import List

import disnake

from nyahbot.util.constants import WaifuState
from models import (
    Waifu,
    Claim,
    NyahPlayer,
    NyahGuild,
)

class Mongo():
    def __init__(self):
        pass

    async def insert_waifu(self, waifu: Waifu) -> None:
        await waifu.insert()
    
    async def update_waifu(self, waifu: Waifu) -> None:
        await waifu.save()

    async def fetch_waifu(self, slug: str) -> Waifu:
        return await Waifu.find_one(Waifu.slug == slug)
    
    async def fetch_waifu_count(self) -> int:
        return await Waifu.count()
    
    async def fetch_random_waifu(self) -> Waifu:
        pipeline = [
            {"$match": {
                "popularity_rank": {"$exists": True},
                "like_rank": {"$exists": True},
                "trash_rank": {"$exists": True}
            }},
            {"$sample": {"size": 1}}
        ]
        result = await Waifu.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=Waifu
        ).to_list()
        return result[0]
    
    async def fetch_waifu_by_name(self, name: str) -> List[Waifu]:
        result = await Waifu.find_many(
            {"name": {"$regex": f"(?i)^{name}"}}
        ).to_list()
        return result



    async def insert_nyah_player(self, nyah_player: NyahPlayer) -> None:
        await nyah_player.insert()

    async def update_nyah_player(self, nyah_player: NyahPlayer) -> None:
        await nyah_player.save()

    async def fetch_nyah_player(self, user: disnake.Member | disnake.User) -> NyahPlayer | None:
        return await NyahPlayer.find_one(NyahPlayer.user_id == user.id)

    

    async def insert_nyah_guild(self, nyah_guild: NyahGuild) -> None:
        await nyah_guild.insert()
    
    async def update_nyah_guild(self, nyah_guild: NyahGuild) -> None:
        await nyah_guild.save()

    async def fetch_nyah_guild(self, guild: disnake.Guild) -> NyahGuild | None:
        return await NyahGuild.find_one(NyahGuild.guild_id == guild.id)



    async def insert_claim(self, claim: Claim) -> None:
        await claim.insert()

    async def update_claim(self, claim: Claim) -> None:
        await claim.save()

    async def fetch_claim(self, uuid: uuid.UUID) -> Claim | None:
        return await Claim.find_one(Claim.id == uuid)

    # async def fetch_claim_by_index(self, user: disnake.Member, index: int) -> Claim | None:
    #     return await Claim.find_one(
    #         (Claim.user_id == user.id) & (Claim.index == index)
    #     )
    


    async def fetch_harem_count(self, user: disnake.Member) -> int:
        return await Claim.find_many({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": {"$nin": [WaifuState.NULL.name, WaifuState.SOLD.name]},
        }).count()

    async def fetch_harem_married_count(self, user: disnake.Member) -> int:
        return await Claim.find_many({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": WaifuState.ACTIVE.name,
        }).count()
    
    async def fetch_harem_unmarried_count(self, user: disnake.Member) -> int:
        return await Claim.find_many({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": WaifuState.INACTIVE.name,
        }).count()
    
    async def fetch_harem_cooldown_count(self, user: disnake.Member) -> int:
        return await Claim.find_many({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": WaifuState.COOLDOWN.name,
        }).count()
    
    async def fetch_harem(self, user: disnake.Member) -> List[Claim]:
        return await Claim.find_many({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": {"$nin": [WaifuState.NULL.name, WaifuState.SOLD.name]},
        }).to_list()
    
    async def fetch_harem_married(self, user: disnake.Member) -> List[Claim]:
        return await Claim.find_many({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": WaifuState.ACTIVE.name,
        }).to_list()
    

import uuid
from typing import List, Any

import disnake
import pymongo

from utils import WaifuState
from models import (
    Waifu,
    Claim,
    NyahPlayer,
    NyahGuild,
    NyahConfig,
)

class Mongo():
    def __init__(self):
        pass

    async def fetch_nyah_config() -> NyahConfig:
        result = await NyahConfig.find().limit(1).to_list()
        return result[0]

    async def update_nyah_config(config: NyahConfig) -> None:
        await config.save()



    async def insert_waifu(self, waifu: Waifu) -> None:
        await waifu.insert()
    
    async def update_waifu(self, waifu: Waifu) -> None:
        await waifu.save()

    async def fetch_waifu(self, slug: str) -> Waifu:
        return await Waifu.find_one(Waifu.slug == slug)
    
    async def fetch_waifu_count(self) -> int:
        return await Waifu.count()
    
    async def fetch_random_waifu(self, aggregations: List = []) -> Waifu:
        pipeline = [
            {"$match": {
                "popularity_rank": {"$exists": True},
                "like_rank": {"$exists": True},
                "trash_rank": {"$exists": True}
            }},
            {"$sort": {"popularity_rank": pymongo.ASCENDING}},
            *aggregations,
            {"$sample": {"size": 1}}
        ]
        result = await Waifu.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=Waifu
        ).to_list()
        return result[0]
    
    async def fetch_random_waifus(self, number: int, aggregations: List = []) -> List[Waifu]:
        pipeline = [
            {"$match": {
                "popularity_rank": {"$exists": True},
                "like_rank": {"$exists": True},
                "trash_rank": {"$exists": True}
            }},
            {"$sort": {"popularity_rank": pymongo.ASCENDING}},
            *aggregations,
            {"$sample": {"size": number}}
        ]
        result = await Waifu.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=Waifu
        ).to_list()
        return result

    async def fetch_waifu_by_name(self, name: str) -> List[Waifu]:
        result = await Waifu.find(
            {"name": {"$regex": f"(?i)^{name}"}}
        ).to_list()
        return result

    async def fetch_waifu_by_name_series(self, name: str, series: str) -> List[Waifu]:
        return await Waifu.find(
            Waifu.name == name,
            Waifu.series == series
        ).sort(
            [(Waifu.popularity_rank, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifu_by_tag(self, tag: str) -> List[Waifu]:
        return await Waifu.find(
            Waifu.tags == tag
        ).sort(
            [(Waifu.popularity_rank, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifu_by_index(self, index: int) -> Waifu:
        #TODO remove this, this is a hack to help scrape each waifu
        return await Waifu.find().skip(index).first_or_none()   

    async def check_waifu_exists(self, slug: str) -> bool:
        return await Waifu.find_one(Waifu.slug == slug) != None

    async def fetch_waifu_series(self) -> List[str]:
        pipeline = [
            {"$unwind": "$series"},
            {"$group": {
                "_id": "$series"
            }}
        ]
        result = await Waifu.aggregate(
            aggregation_pipeline=pipeline
        ).to_list()
        return [doc["_id"] for doc in result]

    async def fetch_waifu_tags(self) -> List[str]:
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {
                "_id": "$tags"
            }}
        ]
        result = await Waifu.aggregate(
            aggregation_pipeline=pipeline
        ).to_list()
        return [doc["_id"] for doc in result]



    async def insert_nyah_player(self, nyah_player: NyahPlayer) -> None:
        await nyah_player.insert()

    async def update_nyah_player(self, nyah_player: NyahPlayer) -> None:
        await nyah_player.save()

    async def fetch_nyah_player(self, user: disnake.Member | disnake.User) -> NyahPlayer | None:
        return await NyahPlayer.find_one(NyahPlayer.user_id == user.id)

    async def fetch_active_nyah_players(self) -> List[NyahPlayer]:
        return await NyahPlayer.find(
            NyahPlayer.score != 0
        ).sort(
            [(NyahPlayer.score, pymongo.DESCENDING)]
        ).to_list()

    async def check_nyah_player_exists(self, user: disnake.Member | disnake.User) -> bool:
        return await NyahPlayer.find_one(NyahPlayer.user_id == user.id) != None

    async def update_all_nyah_players(self, field: str, value: Any) -> None:
        await NyahPlayer.update(
            {"$set": {field: value}}
        )



    async def insert_nyah_guild(self, nyah_guild: NyahGuild) -> None:
        await nyah_guild.insert()
    
    async def update_nyah_guild(self, nyah_guild: NyahGuild) -> None:
        await nyah_guild.save()

    async def fetch_nyah_guild(self, guild: disnake.Guild) -> NyahGuild | None:
        return await NyahGuild.find_one(NyahGuild.guild_id == guild.id)

    async def fetch_nyah_guilds(self) -> List[NyahGuild]:
        return await NyahGuild.find().to_list()

    async def check_nyah_guild_exists(self, guild: disnake.Guild) -> bool:
        return await NyahGuild.find_one(NyahGuild.guild_id == guild.id) != None



    async def insert_claim(self, claim: Claim) -> None:
        await claim.insert()

    async def update_claim(self, claim: Claim) -> None:
        await claim.save()

    async def fetch_claim(self, uuid: uuid.UUID) -> Claim | None:
        return await Claim.find_one(Claim.id == uuid)

    async def fetch_claim_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find(Claim.user_id == user.id).count()
    
    async def fetch_claim_by_index(self, user: disnake.Member | disnake.User, index: int) -> Claim | None:
        result = await Claim.find_one(
            Claim.user_id == user.id,
            Claim.index == index
        ).to_list()
        return result[0] if len(result) > 0 else None
    
    async def fetch_claims_by_slug(self, user: disnake.Member | disnake.User, slug: str) -> List[Claim]:
        return await Claim.find(
            Claim.user_id == user.id,
            Claim.slug == slug
        ).to_list()



    async def fetch_harem_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": {"$nin": [WaifuState.NULL.name, WaifuState.SOLD.name]},
        }).count()

    async def fetch_harem_married_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": WaifuState.ACTIVE.name,
        }).count()
    
    async def fetch_harem_unmarried_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": WaifuState.INACTIVE.name,
        }).count()
    
    async def fetch_harem_cooldown_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": WaifuState.COOLDOWN.name,
        }).count()
    
    async def fetch_harem(self, user: disnake.Member | disnake.User) -> List[Claim]:
        return await Claim.find({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": {"$nin": [WaifuState.NULL.name, WaifuState.SOLD.name]},
        }).to_list()
    
    async def fetch_harem_married(self, user: disnake.Member | disnake.User) -> List[Claim]:
        return await Claim.find({
            "user_id": user.id,
            "index": {"$exists": True},
            "state": {"$exists": True},
            "state": WaifuState.ACTIVE.name,
        }).to_list()
    
    async def fetch_random_harem_married(self, user: disnake.Member | disnake.User) -> Claim:
        pipeline = [
            {"$match": {
                "user_id": user.id,
                "index": {"$exists": True},
                "state": {"$exists": True},
                "state": WaifuState.ACTIVE.name,
            }},
            {"$sample": {"size": 1}}
        ]
        result = await Claim.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=Claim
        ).to_list()
        return result[0]




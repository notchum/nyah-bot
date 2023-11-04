import uuid
from typing import List, Any, Union

import disnake
import pymongo
from beanie.operators import Set, NotIn

from utils import WaifuState
from models import (
    Waifu,
    Claim,
    Harem,
    NyahPlayer,
    NyahGuild,
    NyahConfig,
    Vote,
    Event,
)

class Mongo():
    def __init__(self):
        pass

    async def fetch_nyah_config(self) -> NyahConfig:
        result = await NyahConfig.find_many().to_list()
        return result[0]

    async def update_nyah_config(self, config: NyahConfig) -> None:
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
                "popularity_rank": {"$ne": None},
                "like_rank": {"$ne": None},
                "trash_rank": {"$ne": None}
            }},
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
                "popularity_rank": {"$ne": None},
                "like_rank": {"$ne": None},
                "trash_rank": {"$ne": None}
            }},
            *aggregations,
            {"$sample": {"size": number}}
        ]
        result = await Waifu.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=Waifu
        ).to_list()
        return result

    async def fetch_waifus_by_name(self, name: str) -> List[Waifu]:
        result = await Waifu.find_many(
            {"name": {"$regex": f"(?i)^{name}"}}
        ).to_list()
        return result

    async def fetch_waifus_by_name_and_series(self, name: str, series: str) -> List[Waifu]:
        return await Waifu.find_many(
            Waifu.name == name,
            Waifu.series == series
        ).sort(
            [(Waifu.popularity_rank, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifus_by_series(self, series: str) -> List[Waifu]:
        return await Waifu.find_many(
            Waifu.series == series
        ).sort(
            [(Waifu.name, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifus_by_tag(self, tag: str) -> List[Waifu]:
        return await Waifu.find_many(
            Waifu.tags == tag
        ).sort(
            [(Waifu.name, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifus_birthday_today(self) -> List[Waifu]:
        today = disnake.utils.utcnow().date()
        return await Waifu.find_many(
            Waifu.birthday_month == today.month,
            Waifu.birthday_day == today.day
        ).sort(
            [(Waifu.name, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifu_by_index(self, index: int) -> Waifu:
        #TODO remove this, this is a hack to help scrape each waifu
        return await Waifu.find_many().skip(index).first_or_none()   

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
        return await NyahPlayer.find_many(
            NyahPlayer.score != 0
        ).sort(
            [(NyahPlayer.score, pymongo.DESCENDING)]
        ).to_list()

    async def fetch_all_nyah_players(self) -> List[NyahPlayer]:
        return await NyahPlayer.find_all().sort(
            [(NyahPlayer.score, pymongo.DESCENDING)]
        ).to_list()

    async def check_nyah_player_exists(self, user: disnake.Member | disnake.User) -> bool:
        return await NyahPlayer.find_one(NyahPlayer.user_id == user.id) != None

    async def update_all_nyah_players(self, field: str, value: Any) -> None:
        await NyahPlayer.find_all().update(Set({field: value}))



    async def insert_nyah_guild(self, nyah_guild: NyahGuild) -> None:
        await nyah_guild.insert()
    
    async def update_nyah_guild(self, nyah_guild: NyahGuild) -> None:
        await nyah_guild.save()

    async def fetch_nyah_guild(self, guild: disnake.Guild) -> NyahGuild | None:
        return await NyahGuild.find_one(NyahGuild.guild_id == guild.id)

    async def fetch_nyah_guilds(self) -> List[NyahGuild]:
        return await NyahGuild.find_many().to_list()

    async def check_nyah_guild_exists(self, guild: disnake.Guild) -> bool:
        return await NyahGuild.find_one(NyahGuild.guild_id == guild.id) != None



    async def insert_claim(self, claim: Claim) -> None:
        await claim.insert()

    async def update_claim(self, claim: Claim) -> None:
        await claim.save()

    async def fetch_claim(self, uuid: uuid.UUID) -> Claim | None:
        return await Claim.find_one(Claim.id == uuid)

    async def fetch_claim_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find_many(Claim.user_id == user.id).count()
    
    async def fetch_claim_by_index(self, user: disnake.Member | disnake.User, index: int) -> Claim | None:
        return await Claim.find_one(
            Claim.user_id == user.id,
            Claim.index == index
        )
    
    async def fetch_claims_by_slug(self, user: disnake.Member | disnake.User, slug: str) -> List[Claim]:
        return await Claim.find_many(
            Claim.user_id == user.id,
            Claim.slug == slug
        ).to_list()



    async def fetch_harem_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find_many(
            Claim.user_id == user.id,
            Claim.index != None,
            Claim.state != None,
            NotIn(Claim.state, [WaifuState.NULL.value, WaifuState.SOLD.value]),
        ).count()

    async def fetch_harem_married_count(self, user: Union[disnake.Member, disnake.User, NyahPlayer]) -> int:
        user_id = user.id if isinstance(user, (disnake.Member, disnake.User)) else user.user_id
        return await Claim.find_many(
            Claim.user_id == user_id,
            Claim.index != None,
            Claim.state == WaifuState.ACTIVE.value,
        ).count()
    
    async def fetch_harem_unmarried_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find_many(
            Claim.user_id == user.id,
            Claim.index != None,
            Claim.state == WaifuState.INACTIVE.value,
        ).count()
    
    async def fetch_harem_cooldown_count(self, user: disnake.Member | disnake.User) -> int:
        return await Claim.find_many(
            Claim.user_id == user.id,
            Claim.index != None,
            Claim.state == WaifuState.COOLDOWN.value,
        ).count()
    
    async def fetch_harem(self, user: disnake.Member | disnake.User) -> Harem:
        result = await Claim.find_many(
            Claim.user_id == user.id,
            Claim.index != None,
            Claim.state != None,
            NotIn(Claim.state, [WaifuState.NULL.value, WaifuState.SOLD.value]),
        ).sort(
            [(Claim.index, pymongo.ASCENDING)]
        ).to_list()
        return Harem(result)
    
    async def fetch_harem_married(self, user: disnake.Member | disnake.User) -> Harem:
        result = await Claim.find_many(
            Claim.user_id == user.id,
            Claim.index != None,
            Claim.state == WaifuState.ACTIVE.value,
        ).sort(
            [(Claim.index, pymongo.ASCENDING)]
        ).to_list()
        return Harem(result)
    
    async def fetch_random_harem_married(self, user: disnake.Member | disnake.User) -> Claim:
        pipeline = [
            {"$match": {
                "user_id": user.id,
                "index": {"$ne": None},
                "state": {"$ne": None},
                "state": WaifuState.ACTIVE.value,
            }},
            {"$sample": {"size": 1}}
        ]
        result = await Claim.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=Claim
        ).to_list()
        return result[0]



    async def fetch_active_war(self, guild: disnake.Guild) -> Event | None:
        return await Event.find_one(
            Event.guild_id == guild.id,
            Event.state == disnake.GuildScheduledEventStatus.scheduled.value,
        )

    async def insert_vote(self, vote: Vote) -> None:
        await vote.insert()

    async def fetch_and_delete_vote(self, user: disnake.Member | disnake.User, battle_id: uuid.UUID) -> None:
        await Vote.find_one(
            Vote.user_id == user.id,
            Vote.battle_id == battle_id
        ).delete()

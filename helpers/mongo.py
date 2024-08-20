import uuid
from typing import List, Any, Union

import disnake
import pymongo
from beanie.operators import Set, NotIn

import models
from utils.constants import WaifuState


class Mongo():
    def __init__(self):
        pass

    async def fetch_nyah_config(self) -> models.NyahConfig:
        result = await models.NyahConfig.find_many().to_list()
        return result[0]

    async def update_nyah_config(self, config: models.NyahConfig) -> None:
        await config.save()



    async def insert_waifu(self, waifu: models.Waifu) -> None:
        await waifu.insert()
    
    async def update_waifu(self, waifu: models.Waifu) -> None:
        await waifu.save()

    async def fetch_waifu(self, slug: str) -> models.Waifu:
        return await models.Waifu.find_one(models.Waifu.slug == slug)
    
    async def fetch_waifu_count(self) -> int:
        return await models.Waifu.count()
    
    async def fetch_random_waifu(self, aggregations: List = []) -> models.Waifu:
        pipeline = [
            {"$match": {
                "popularity_rank": {"$ne": None},
                "like_rank": {"$ne": None},
                "trash_rank": {"$ne": None}
            }},
            *aggregations,
            {"$sample": {"size": 1}}
        ]
        result = await models.Waifu.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=models.Waifu
        ).to_list()
        return result[0]
    
    async def fetch_random_waifus(self, number: int, aggregations: List = []) -> List[models.Waifu]:
        pipeline = [
            {"$match": {
                "popularity_rank": {"$ne": None},
                "like_rank": {"$ne": None},
                "trash_rank": {"$ne": None}
            }},
            *aggregations,
            {"$sample": {"size": number}}
        ]
        result = await models.Waifu.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=models.Waifu
        ).to_list()
        return result

    async def fetch_waifus_by_name(self, name: str) -> List[models.Waifu]:
        result = await models.Waifu.find_many(
            {"name": {"$regex": f"(?i)^{name}"}}
        ).to_list()
        return result

    async def fetch_waifus_by_name_and_series(self, name: str, series: str) -> List[models.Waifu]:
        return await models.Waifu.find_many(
            models.Waifu.name == name,
            models.Waifu.series == series
        ).sort(
            [(models.Waifu.popularity_rank, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifus_by_series(self, series: str) -> List[models.Waifu]:
        return await models.Waifu.find_many(
            models.Waifu.series == series
        ).sort(
            [(models.Waifu.name, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifus_by_tag(self, tag: str) -> List[models.Waifu]:
        return await models.Waifu.find_many(
            models.Waifu.tags == tag
        ).sort(
            [(models.Waifu.name, pymongo.ASCENDING)]
        ).to_list()

    async def fetch_waifus_birthday_today(self) -> List[models.Waifu]:
        today = disnake.utils.utcnow().date()
        return await models.Waifu.find_many(
            models.Waifu.birthday_month == today.month,
            models.Waifu.birthday_day == today.day
        ).sort(
            [(models.Waifu.name, pymongo.ASCENDING)]
        ).to_list()

    async def check_waifu_exists(self, slug: str) -> bool:
        return await models.Waifu.find_one(models.Waifu.slug == slug) != None

    async def fetch_waifu_series(self) -> List[str]:
        pipeline = [
            {"$unwind": "$series"},
            {"$group": {
                "_id": "$series"
            }}
        ]
        result = await models.Waifu.aggregate(
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
        result = await models.Waifu.aggregate(
            aggregation_pipeline=pipeline
        ).to_list()
        return [doc["_id"] for doc in result]



    async def insert_nyah_player(self, nyah_player: models.NyahPlayer) -> None:
        await nyah_player.insert()

    async def update_nyah_player(self, nyah_player: models.NyahPlayer) -> None:
        await nyah_player.save()

    async def fetch_nyah_player(self, user: disnake.Member | disnake.User) -> models.NyahPlayer | None:
        return await models.NyahPlayer.find_one(models.NyahPlayer.user_id == user.id)

    async def fetch_active_nyah_players(self) -> List[models.NyahPlayer]:
        return await models.NyahPlayer.find_many(
            models.NyahPlayer.score != 0
        ).sort(
            [(models.NyahPlayer.score, pymongo.DESCENDING)]
        ).to_list()

    async def fetch_all_nyah_players(self) -> List[models.NyahPlayer]:
        return await models.NyahPlayer.find_all().sort(
            [(models.NyahPlayer.score, pymongo.DESCENDING)]
        ).to_list()

    async def check_nyah_player_exists(self, user: disnake.Member | disnake.User) -> bool:
        return await models.NyahPlayer.find_one(models.NyahPlayer.user_id == user.id) != None

    async def update_all_nyah_players(self, field: str, value: Any) -> None:
        await models.NyahPlayer.find_all().update(Set({field: value}))



    async def insert_nyah_guild(self, nyah_guild: models.NyahGuild) -> None:
        await nyah_guild.insert()
    
    async def update_nyah_guild(self, nyah_guild: models.NyahGuild) -> None:
        await nyah_guild.save()

    async def fetch_nyah_guild(self, guild: disnake.Guild) -> models.NyahGuild | None:
        return await models.NyahGuild.find_one(models.NyahGuild.guild_id == guild.id)

    async def fetch_nyah_guilds(self) -> List[models.NyahGuild]:
        return await models.NyahGuild.find_many().to_list()

    async def check_nyah_guild_exists(self, guild: disnake.Guild) -> bool:
        return await models.NyahGuild.find_one(models.NyahGuild.guild_id == guild.id) != None



    async def insert_claim(self, claim: models.Claim) -> None:
        await claim.insert()

    async def update_claim(self, claim: models.Claim) -> None:
        await claim.save()

    async def fetch_claim(self, uuid: uuid.UUID) -> models.Claim | None:
        return await models.Claim.find_one(models.Claim.id == uuid)

    async def fetch_claim_count(self, user: disnake.Member | disnake.User) -> int:
        return await models.Claim.find_many(models.Claim.user_id == user.id).count()
    
    async def fetch_claim_by_index(self, user: disnake.Member | disnake.User, index: int) -> models.Claim | None:
        return await models.Claim.find_one(
            models.Claim.user_id == user.id,
            models.Claim.index == index
        )
    
    async def fetch_claims_by_slug(self, user: disnake.Member | disnake.User, slug: str) -> List[models.Claim]:
        return await models.Claim.find_many(
            models.Claim.user_id == user.id,
            models.Claim.slug == slug
        ).to_list()

    async def update_all_claims(self, field: str, value: Any) -> None:
        await models.Claim.find_all().update(Set({field: value}))


    async def fetch_harem_count(self, user: disnake.Member | disnake.User) -> int:
        return await models.Claim.find_many(
            models.Claim.user_id == user.id,
            models.Claim.index != None,
            models.Claim.state != None,
            NotIn(models.Claim.state, [WaifuState.NULL, WaifuState.SOLD, WaifuState.FUSED]),
        ).count()

    async def fetch_harem_married_count(self, user: Union[disnake.Member, disnake.User, models.NyahPlayer]) -> int:
        user_id = user.id if isinstance(user, (disnake.Member, disnake.User)) else user.user_id
        return await models.Claim.find_many(
            models.Claim.user_id == user_id,
            models.Claim.index != None,
            models.Claim.state == WaifuState.ACTIVE,
        ).count()
    
    async def fetch_harem_unmarried_count(self, user: disnake.Member | disnake.User) -> int:
        return await models.Claim.find_many(
            models.Claim.user_id == user.id,
            models.Claim.index != None,
            models.Claim.state == WaifuState.INACTIVE,
        ).count()
    
    async def fetch_harem_cooldown_count(self, user: disnake.Member | disnake.User) -> int:
        return await models.Claim.find_many(
            models.Claim.user_id == user.id,
            models.Claim.index != None,
            models.Claim.state == WaifuState.COOLDOWN,
        ).count()
    
    async def fetch_harem(self, user: disnake.Member | disnake.User) -> models.Harem:
        result = await models.Claim.find_many(
            models.Claim.user_id == user.id,
            models.Claim.index != None,
            models.Claim.state != None,
            NotIn(models.Claim.state, [WaifuState.NULL, WaifuState.SOLD, WaifuState.FUSED]),
        ).sort(
            [(models.Claim.index, pymongo.ASCENDING)]
        ).to_list()
        return models.Harem(result)
    
    async def fetch_harem_married(self, user: disnake.Member | disnake.User) -> models.Harem:
        result = await models.Claim.find_many(
            models.Claim.user_id == user.id,
            models.Claim.index != None,
            models.Claim.state == WaifuState.ACTIVE,
        ).sort(
            [(models.Claim.index, pymongo.ASCENDING)]
        ).to_list()
        return models.Harem(result)
    
    async def fetch_random_harem_married(self, user: disnake.Member | disnake.User) -> models.Claim:
        pipeline = [
            {"$match": {
                "user_id": user.id,
                "index": {"$ne": None},
                "state": {"$ne": None},
                "state": WaifuState.ACTIVE,
            }},
            {"$sample": {"size": 1}}
        ]
        result = await models.Claim.aggregate(
            aggregation_pipeline=pipeline,
            projection_model=models.Claim
        ).to_list()
        return result[0]



    async def fetch_active_war(self, guild: disnake.Guild) -> models.Event | None:
        return await models.Event.find_one(
            models.Event.guild_id == guild.id,
            models.Event.state == disnake.GuildScheduledEventStatus.scheduled.value,
        )

    async def insert_vote(self, vote: models.Vote) -> None:
        await vote.insert()

    async def fetch_and_delete_vote(self, user: disnake.Member | disnake.User, battle_id: uuid.UUID) -> None:
        await models.Vote.find_one(
            models.Vote.user_id == user.id,
            models.Vote.battle_id == battle_id
        ).delete()

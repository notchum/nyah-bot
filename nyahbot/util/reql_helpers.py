from typing import List

import disnake
from rethinkdb import r

from nyahbot.util.globals import conn
from nyahbot.util.constants import WaifuState
from nyahbot.util.dataclasses import (
    NyahGuild,
    NyahPlayer,
    Waifu,
    Claim,
)

##*************************************************##
##********              General             *******##
##*************************************************##

async def get_rethink_uuid() -> str:
    return r.uuid().run(conn)

##*************************************************##
##********             NyahGuild            *******##
##*************************************************##

async def get_nyah_guild(guild: disnake.Guild) -> NyahGuild | None:
    result = r.db("nyah") \
                .table("guilds") \
                .get(str(guild.id)) \
                .run(conn)
    if result == None:
        return None
    return NyahGuild(**result)

async def set_nyah_guild(nyah_guild: NyahGuild) -> None:
    result = r.db("nyah") \
                .table("guilds") \
                .get(str(nyah_guild.guild_id)) \
                .update(nyah_guild.__dict__) \
                .run(conn)
    if result["errors"] > 0:
        raise Exception # TODO create custom exception
    return

##*************************************************##
##********             NyahPlayer           *******##
##*************************************************##

async def get_nyah_player(user: disnake.Member) -> NyahPlayer | None:
    result = r.db("nyah") \
                .table("players") \
                .get_all([str(user.guild.id), str(user.id)], index="guild_user") \
                .nth(0) \
                .run(conn)
    if result == None:
        return None
    return NyahPlayer(**result)

async def get_nyah_player_guild(guild: disnake.Guild) -> List[NyahPlayer] | None:
    result = r.db("nyah") \
                .table("players") \
                .get_all(str(guild.id), index="guild_id") \
                .order_by(r.desc("score")) \
                .run(conn)
    if result == None:
        return None
    return [NyahPlayer(**doc) for doc in result]

async def set_nyah_player(nyah_player: NyahPlayer) -> None:
    result = r.db("nyah") \
                .table("players") \
                .get_all([nyah_player.guild_id, nyah_player.user_id], index="guild_user") \
                .update(nyah_player.__dict__) \
                .run(conn)
    if result["errors"] > 0:
        raise Exception # TODO create custom exception
    return

##*************************************************##
##********             Waifu                *******##
##*************************************************##

async def get_waifu_core_size() -> int:
    return r.db("waifus") \
            .table("core") \
            .count() \
            .run(conn)

async def get_waifu_core(slug: str) -> Waifu | None:
    result = r.db("waifus") \
                .table("core") \
                .get(slug) \
                .run(conn)
    if result == None:
        return None
    return Waifu(**result)

async def get_waifu_core_name(name: str) -> List[Waifu]:
    result = r.db("waifus") \
                .table("core") \
                .filter(
                    r.row["name"].match(f"(?i)^{name}")
                ) \
                .run(conn)
    return [Waifu(**doc) for doc in result]

async def get_waifu_core_random(number: int) -> Waifu | List[Waifu]:
    result = r.db("waifus") \
                .table("core") \
                .has_fields(["popularity_rank", "like_rank", "trash_rank"]) \
                .sample(number) \
                .run(conn)
    if number > 1:
        return [Waifu(**doc) for doc in result]
    return Waifu(**result[0])

##*************************************************##
##********             Claim                *******##
##*************************************************##

async def get_waifu_claim_size(user: disnake.Member) -> int:
    return  r.db("waifus") \
                .table("claims") \
                .get_all(str(user.id), index="user_id") \
                .count() \
                .run(conn)

async def get_waifu_claim(id: str) -> Claim | None:
    result = r.db("waifus") \
                .table("claims") \
                .get(id) \
                .run(conn)
    if result == None:
        return None
    return Claim(**result)

async def get_waifu_claim_index(user: disnake.Member, index: int) -> Claim | None:
    """ 1-based index. """
    result = r.db("waifus") \
                .table("claims") \
                .get_all([str(user.guild.id), str(user.id)], index="guild_user") \
                .has_fields(["state", "index"]) \
                .order_by("index") \
                .nth(index - 1) \
                .run(conn)
    if result == None:
        return None
    return Claim(**result)

async def get_waifu_claims_slug(user: disnake.Member, slug: str) -> List[Claim]:
    result = r.db("waifus") \
                .table("claims") \
                .get_all(str(user.id), index="user_id") \
                .filter({"slug": slug}) \
                .run(conn)
    return [Claim(**doc) for doc in result]

async def set_waifu_claim(claim: Claim) -> None:
    result = r.db("waifus") \
                .table("claims") \
                .get(claim.id) \
                .update(claim.__dict__) \
                .run(conn)
    if result["errors"] > 0:
        raise Exception # TODO create custom exception
    return

async def insert_waifu_claim(claim: Claim) -> None:
    result = r.db("waifus") \
                .table("claims") \
                .insert(claim.__dict__) \
                .run(conn)
    if result["errors"] > 0:
        raise Exception # TODO create custom exception
    return

##*************************************************##
##********             Harem                *******##
##*************************************************##

async def get_harem_size(guild: disnake.Guild, user: disnake.User | disnake.Member) -> int:
    return r.db("waifus") \
            .table("claims") \
            .get_all([str(guild.id), str(user.id)], index="guild_user") \
            .has_fields(["state", "index"]) \
            .filter(
                r.or_(
                    r.row["state"].ne(WaifuState.NULL.name),
                    r.row["state"].ne(WaifuState.SOLD.name),
                )
            ) \
            .count() \
            .run(conn)

async def get_harem_married_size(guild: disnake.Guild, user: disnake.User | disnake.Member) -> int:
    return r.db("waifus") \
            .table("claims") \
            .get_all([str(guild.id), str(user.id)], index="guild_user") \
            .has_fields(["state", "index"]) \
            .filter(
                r.row["state"].eq(WaifuState.ACTIVE.name)
            ) \
            .count() \
            .run(conn)

async def get_harem_unmarried_size(guild: disnake.Guild, user: disnake.User | disnake.Member) -> int:
    return r.db("waifus") \
            .table("claims") \
            .get_all([str(guild.id), str(user.id)], index="guild_user") \
            .has_fields(["state", "index"]) \
            .filter(
                r.row["state"].eq(WaifuState.INACTIVE.name)
            ) \
            .count() \
            .run(conn)

async def get_harem_cooldown_size(guild: disnake.Guild, user: disnake.User | disnake.Member) -> int:
    return r.db("waifus") \
            .table("claims") \
            .get_all([str(guild.id), str(user.id)], index="guild_user") \
            .has_fields(["state", "index"]) \
            .filter(
                r.row["state"].eq(WaifuState.COOLDOWN.name)
            ) \
            .count() \
            .run(conn)

async def get_harem(guild: disnake.Guild, user: disnake.User | disnake.Member) -> List[Claim]:
    result =  r.db("waifus") \
                .table("claims") \
                .get_all([str(guild.id), str(user.id)], index="guild_user") \
                .has_fields(["state", "index"]) \
                .filter(
                    r.or_(
                        r.row["state"].ne(WaifuState.NULL.name),
                        r.row["state"].ne(WaifuState.SOLD.name),
                    )
                ) \
                .order_by("index") \
                .run(conn)
    return [Claim(**doc) for doc in result]

async def get_harem_married(guild: disnake.Guild, user: disnake.User | disnake.Member) -> List[Claim]:
    result =  r.db("waifus") \
                .table("claims") \
                .get_all([str(guild.id), str(user.id)], index="guild_user") \
                .has_fields(["state", "index"]) \
                .filter(
                    r.row["state"].eq(WaifuState.ACTIVE.name)
                ) \
                .order_by("index") \
                .run(conn)
    return [Claim(**doc) for doc in result]
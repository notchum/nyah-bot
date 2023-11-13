import asyncio
import random
from typing import Optional

from rethinkdb import r
conn = r.connect(host="99.104.109.35")

import pymongo
import disnake
import motor.motor_asyncio
from beanie import init_beanie, Document
from pydantic import Field, BaseModel
from uuid import uuid4, UUID
import datetime

from utils import WaifuState
import utils.traits as traits
from models import *

async def test():
    print("test")

class Foo(object):
    @classmethod
    async def create(cls, settings):
        self = Foo()
        self.settings = settings
        await test()
        return self


def convert_state_str_to_int(s: str) -> int:
    # convert a WaifuState string to an int
    # i.e. "ACTIVE" -> 1
    return WaifuState[s].value

async def main():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb+srv://notchum:mVCx70b2GeIRHmDo@cluster0.tz1fikf.mongodb.net/')
    await init_beanie(client["nyah"], document_models=[NyahPlayer, NyahConfig, NyahGuild])
    await init_beanie(client["waifus"], document_models=[Waifu])
    await init_beanie(client["waifus"], document_models=[Claim])
    await init_beanie(client["wars"], document_models=[Event])


    # result = r.db("nyah").table("players").run(conn)
    # for i, doc in enumerate(result):
    #     if doc["guild_id"] == "776929597567795247":
    #         continue
    #     doc = NyahPlayer(
    #         user_id=int(doc["user_id"]),
    #         name=doc["name"],
    #         score=int(doc["score"]),
    #         level=int(doc["level"]),
    #         xp=int(doc["xp"]),
    #         money=int(doc["money"]),
    #         wishlist=doc["wishlist"],
    #         timestamp_last_claim=doc["timestamp_last_claim"].isoformat() if doc["timestamp_last_claim"] else None,
    #         timestamp_last_duel=doc["timestamp_last_duel"].isoformat() if doc["timestamp_last_duel"] else None,
    #         timestamp_last_minigame=doc["timestamp_last_minigame"].isoformat() if doc["timestamp_last_minigame"] else None,
    #     )
    #     print(f"{i} - {doc.name} - {doc.user_id}")
    #     await doc.insert()
    
    # result = r.db("waifus").table("claims").run(conn)
    # i = 0
    # for doc in result:
    #     if doc["guild_id"] == "776929597567795247":
    #         continue
    #     if doc["user_id"] in ["1166101264191455252", "776673099382128661"]:
    #         continue
    #     doc = Claim(
    #         id=UUID(doc["id"]),
    #         slug=doc["slug"],
    #         guild_id=int(doc["guild_id"]),
    #         channel_id=int(doc["channel_id"]),
    #         message_id=int(doc["message_id"]),
    #         user_id=int(doc["user_id"]),
    #         jump_url=doc["jump_url"],
    #         image_url=doc["image_url"],
    #         cached_images_urls=doc["cached_images_urls"] if doc["cached_images_urls"] else [],
    #         state=convert_state_str_to_int(doc["state"]) if isinstance(doc["state"], str) else doc["state"],
    #         index=int(doc["index"]) if doc["index"] else None,
    #         price=int(doc["price"]),
    #         attack=int(doc["attack"]),
    #         defense=int(doc["defense"]),
    #         health=int(doc["health"]),
    #         speed=int(doc["speed"]),
    #         magic=int(doc["magic"]),
    #         attack_mod=int(doc["attack_mod"]),
    #         defense_mod=int(doc["defense_mod"]),
    #         health_mod=int(doc["health_mod"]),
    #         speed_mod=int(doc["speed_mod"]),
    #         magic_mod=int(doc["magic_mod"]),
    #         trait_common=doc["trait_common"],
    #         trait_uncommon=doc["trait_uncommon"],
    #         trait_rare=doc["trait_rare"],
    #         trait_legendary=doc["trait_legendary"],
    #         timestamp=doc["timestamp"].isoformat() if doc["timestamp"] else None,
    #         timestamp_cooldown=doc["timestamp_cooldown"].isoformat() if doc["timestamp_cooldown"] else None,
    #     )
    #     print(f"{i} - {doc.slug} - {doc.user_id} - {doc.id}")
    #     await doc.insert()
    #     i += 1

asyncio.run(main())
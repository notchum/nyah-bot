from enum import Enum
from typing import List

import disnake

from models import NyahPlayer
from helpers import Mongo
from utils import Emojis

mongo = Mongo()

class ItemTypes(Enum):
    ITEM_CHEST_KEY    = 1
    ITEM_TRAIT_SCROLL = 2
    ITEM_SHONEN_STONE = 3
    ITEM_ENERGY_BOOST = 4

class Prices(Enum):
    ITEM_CHEST_KEY    = 10000
    ITEM_TRAIT_SCROLL = 10000
    ITEM_SHONEN_STONE = 10000
    ITEM_ENERGY_BOOST = 10000

##*************************************************##
##********            SHOP ITEMS            *******##
##*************************************************##

class ShopBaseItem():
    def __init__(
        self,
        name: str,
        type: ItemTypes,
        price: int,
        emoji: str
    ):
        self.name = name
        self.type = type
        self.price = price
        self.emoji = emoji

    @property
    def shop_str(self):
        return f"`{self.emoji}` **__{self.name}__** - `{self.price:,}` {Emojis.COINS}"

    @property
    def buy_str(self):
        return f"{self.emoji} {self.name} (Price: {self.price:,})"


class ShopChestItem(ShopBaseItem):
    def __init__(self):
        super().__init__(
            name="Chest",
            type=ItemTypes.ITEM_CHEST_KEY,
            price=Prices.ITEM_CHEST_KEY.value,
            emoji=Emojis.ITEM_CHEST_KEY,
        )


class ShopTraitScrollItem(ShopBaseItem):
    def __init__(self):
        super().__init__(
            name="Trait Scroll",
            type=ItemTypes.ITEM_TRAIT_SCROLL,
            price=Prices.ITEM_TRAIT_SCROLL.value,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
        )


SHOP_ITEMS: List[ShopBaseItem] = [
    ShopChestItem(),
    ShopTraitScrollItem(),
]

def get_shop_item(item_type: ItemTypes | int) -> ShopBaseItem:
    if isinstance(item_type, int):
        item_type = ItemTypes(item_type)
    for item in SHOP_ITEMS:
        if item.type == item_type:
            return item
    raise ValueError(f"Item type {item_type} not found in shop items")

##*************************************************##
##********          PLAYER ITEMS            *******##
##*************************************************##

class PlayerBaseItem():
    def __init__(
        self,
        name: str,
        type: ItemTypes,
        emoji: str,
        owner: NyahPlayer,
        amount: int
    ):
        self.name = name
        self.type = type
        self.emoji = emoji
        self.owner = owner
        self.amount = amount

    @property
    def inv_str(self):
        return f"{self.emoji} x{self.amount}"

    async def use(self) -> None:
        await self.owner.remove_inventory_item(self.type.value, 1)


class PlayerChestItem(PlayerBaseItem):
    def __init__(self, owner: NyahPlayer, amount: int):
        super().__init__(
            name="Chest",
            type=ItemTypes.ITEM_CHEST_KEY,
            emoji=Emojis.ITEM_CHEST_KEY,
            owner=owner,
            amount=amount
        )

    async def use(self, inter: disnake.ApplicationCommandInteraction) -> None:
        chest_size = 3
        result = await mongo.fetch_random_waifus(
            number=chest_size,
            aggregations=[
                {"$match": {
                    "popularity_rank": {"$lt": 3000}
                }}
            ]
        )

        description = ""
        embeds = []
        claims = []
        for waifu in result:
            claim = await self.owner.generate_claim(waifu)
            await mongo.insert_claim(claim)
            claims.append(claim)
            
            embed = disnake.Embed(
                title="Chest",
                color=disnake.Color.fuchsia(),
                url="https://www.youtube.com/watch?v=Uj9SAdIGfdw"
            )
            embed.set_image(url=waifu.image_url)
            embeds.append(embed)
            
            description += f"- __**{waifu.name}**__ ({claim.stats_str}) | {claim.price_str}\n"
        
        for embed in embeds:
            embed.description = description

        message = await inter.edit_original_response(embeds=embeds)

        for claim in claims:
            claim.guild_id=message.guild.id
            claim.channel_id=message.channel.id
            claim.message_id=message.id
            claim.jump_url=message.jump_url
            claim.timestamp=message.created_at
            await mongo.update_claim(claim)
        
        await super().use()


class PlayerTraitScrollItem(PlayerBaseItem):
    def __init__(self, owner: NyahPlayer, amount: int):
        super().__init__(
            name="Trait Scroll",
            type=ItemTypes.ITEM_TRAIT_SCROLL,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
            owner=owner,
            amount=amount
        )

    async def use(self, inter: disnake.ApplicationCommandInteraction):
        return
        await super().use()

class PlayerShonenStoneItem(PlayerBaseItem):
    def __init__(self, owner: NyahPlayer, amount: int):
        super().__init__(
            name="Trait Scroll",
            type=ItemTypes.ITEM_TRAIT_SCROLL,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
            owner=owner,
            amount=amount
        )

    async def use(self, inter: disnake.ApplicationCommandInteraction):
        return
        await super().use()


class PlayerEnergyBoostItem(PlayerBaseItem):
    def __init__(self, owner: NyahPlayer, amount: int):
        super().__init__(
            name="Trait Scroll",
            type=ItemTypes.ITEM_TRAIT_SCROLL,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
            owner=owner,
            amount=amount
        )

    async def use(self, inter: disnake.ApplicationCommandInteraction):
        return
        await super().use()


class ItemFactory:
    @staticmethod
    def create_item(item_type: int, owner: NyahPlayer, amount: int):
        match ItemTypes(item_type):
            case ItemTypes.ITEM_CHEST_KEY:
                return PlayerChestItem(owner, amount)
            case ItemTypes.ITEM_TRAIT_SCROLL:
                return PlayerTraitScrollItem(owner, amount)
            case ItemTypes.ITEM_SHONEN_STONE:
                return PlayerShonenStoneItem(owner, amount)
            case ItemTypes.ITEM_ENERGY_BOOST:
                return PlayerEnergyBoostItem(owner, amount)
            case _:
                raise ValueError(f"Unsupported item type: {item_type}")

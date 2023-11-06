from enum import Enum
from typing import List

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

    async def use(self):
        pass


class PlayerChestItem(PlayerBaseItem):
    def __init__(self, owner: NyahPlayer, amount: int):
        super().__init__(
            name="Chest",
            type=ItemTypes.ITEM_CHEST_KEY,
            emoji=Emojis.ITEM_CHEST_KEY,
            owner=owner,
            amount=amount
        )

    async def use(self):
        # chest_size = 3
        # result = await mongo.fetch_random_waifus(chest_size)
        # for waifu in result:
        #     self.owner.generate_claim(waifu)
        pass


class PlayerTraitScrollItem(PlayerBaseItem):
    def __init__(self, owner: NyahPlayer, amount: int):
        super().__init__(
            name="Trait Scroll",
            type=ItemTypes.ITEM_TRAIT_SCROLL,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
            owner=owner,
            amount=amount
        )

    async def use(self):
        pass

class PlayerShonenStoneItem(PlayerBaseItem):
    def __init__(self, owner: NyahPlayer, amount: int):
        super().__init__(
            name="Trait Scroll",
            type=ItemTypes.ITEM_TRAIT_SCROLL,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
            owner=owner,
            amount=amount
        )

    async def use(self):
        pass


class PlayerEnergyBoostItem(PlayerBaseItem):
    def __init__(self, owner: NyahPlayer, amount: int):
        super().__init__(
            name="Trait Scroll",
            type=ItemTypes.ITEM_TRAIT_SCROLL,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
            owner=owner,
            amount=amount
        )

    async def use(self):
        pass


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

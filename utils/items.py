from enum import Enum
from typing import List

import disnake

import models
from helpers import Mongo, WaifuHaremEmbed
from utils.constants import Emojis, Prices, ItemTypes, TIER_TITLE_MAP
from views import CharacterSelectView

mongo = Mongo()

##*************************************************##
##********            SHOP ITEMS            *******##
##*************************************************##

class ShopBaseItem():
    def __init__(
        self,
        name: str,
        type_: ItemTypes,
        price: Prices,
        emoji: str
    ):
        self.name = name
        self.type = type_
        self.price = price.value
        self.emoji = emoji

    @property
    def shop_str(self):
        return f"`{self.emoji}` **__{self.name}__** - `{self.price:,}` {Emojis.TICKET}"

    @property
    def buy_str(self):
        return f"{self.emoji} {self.name} (Price: {self.price:,})"


class ShopChestItem(ShopBaseItem):
    def __init__(self):
        super().__init__(
            name="Chest",
            type_=ItemTypes.ITEM_CHEST_KEY,
            price=Prices.COST_ITEM_CHEST_KEY,
            emoji=Emojis.ITEM_CHEST_KEY,
        )


class ShopTraitScrollItem(ShopBaseItem):
    def __init__(self):
        super().__init__(
            name="Trait Scroll",
            type_=ItemTypes.ITEM_TRAIT_SCROLL,
            price=Prices.COST_ITEM_TRAIT_SCROLL,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
        )


class ShopShonenStoneItem(ShopBaseItem):
    def __init__(self):
        super().__init__(
            name="Shonen Stone",
            type_=ItemTypes.ITEM_SHONEN_STONE,
            price=Prices.COST_ITEM_SHONEN_STONE,
            emoji=Emojis.ITEM_SHONEN_STONE,
        )


class ShopHealthTeaItem(ShopBaseItem):
    def __init__(self):
        super().__init__(
            name="Health Tea",
            type_=ItemTypes.ITEM_HEALTH_TEA,
            price=Prices.COST_ITEM_HEALTH_TEA,
            emoji=Emojis.ITEM_HEALTH_TEA,
        )


SHOP_ITEMS: List[ShopBaseItem] = [
    ShopChestItem(),
    ShopTraitScrollItem(),
    ShopShonenStoneItem(),
    ShopHealthTeaItem(),
]

def get_shop_item(item_type: ItemTypes) -> ShopBaseItem:
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
        type_: ItemTypes,
        emoji: str,
        owner: models.NyahPlayer,
        amount: int
    ):
        self.name = name
        self.type = type_
        self.emoji = emoji
        self.owner = owner
        self.amount = amount

    @property
    def inv_str(self):
        return f"{self.emoji} x{self.amount}"

    async def use(self, inter: disnake.ApplicationCommandInteraction):
        harem = await mongo.fetch_harem(inter.author)

        embed = disnake.Embed(
            title=f"{self.name} {self.emoji}",
            description=f"You have `x{self.amount}` {self.name}s available to use.\n\n"
                        f"Please select a character to use the {self.name} on.\n\n"
                        f"Once your desired character is selected, click **Confirm** {Emojis.CHECK_MARK}.",
            color=disnake.Color.fuchsia()
        )
        waifu_dropdown = CharacterSelectView(inter.author, harem)
        message = await inter.edit_original_response(embed=embed, view=waifu_dropdown)
        waifu_dropdown.message = message
        waifu_dropdown.selected_claim = None

        await waifu_dropdown.wait()

        if isinstance(waifu_dropdown.selected_claim, models.Claim):
            claim = waifu_dropdown.selected_claim

            match self.type:
                case ItemTypes.ITEM_TRAIT_SCROLL:
                    claim.roll_trait()
                case ItemTypes.ITEM_SHONEN_STONE:
                    claim.roll_skills()
                case ItemTypes.ITEM_HEALTH_TEA:
                    claim.reset_hp()
                case _:
                    raise ValueError(f"Unsupported item type: {self.type}")
            
            await mongo.update_claim(claim)
            waifu = await mongo.fetch_waifu(claim.slug)

            await self.owner.remove_inventory_item(self.type, 1)
            self.amount -= 1

            embed = disnake.Embed(
                title=f"{self.name} {self.emoji}",
                description=f"{self.name} successfully applied to **__{claim.name}__**.\n\n"
                            f"You now have `x{self.amount}` {self.name}s available to use.",
                color=disnake.Color.green()
            )
            await inter.edit_original_response(
                embeds=[embed, WaifuHaremEmbed(waifu, claim)]
            )


class PlayerChestItem(PlayerBaseItem):
    def __init__(self, owner: models.NyahPlayer, amount: int):
        super().__init__(
            name="Chest",
            type_=ItemTypes.ITEM_CHEST_KEY,
            emoji=Emojis.ITEM_CHEST_KEY,
            owner=owner,
            amount=amount
        )

    async def use(self, inter: disnake.ApplicationCommandInteraction):
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
            
            description += f"- __**{waifu.name}**__ ({claim.skill_str_short}) | {TIER_TITLE_MAP[claim.tier]}\n"
        
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
        
        await self.owner.remove_inventory_item(self.type, 1)
        self.amount -= 1


class PlayerTraitScrollItem(PlayerBaseItem):
    def __init__(self, owner: models.NyahPlayer, amount: int):
        super().__init__(
            name="Trait Scroll",
            type_=ItemTypes.ITEM_TRAIT_SCROLL,
            emoji=Emojis.ITEM_TRAIT_SCROLL,
            owner=owner,
            amount=amount
        )

    async def use(self, inter: disnake.ApplicationCommandInteraction):
        await super().use(inter)


class PlayerShonenStoneItem(PlayerBaseItem):
    def __init__(self, owner: models.NyahPlayer, amount: int):
        super().__init__(
            name="Shonen Stone",
            type_=ItemTypes.ITEM_SHONEN_STONE,
            emoji=Emojis.ITEM_SHONEN_STONE,
            owner=owner,
            amount=amount
        )

    async def use(self, inter: disnake.ApplicationCommandInteraction):
        await super().use(inter)


class PlayerHealthTeaItem(PlayerBaseItem):
    def __init__(self, owner: models.NyahPlayer, amount: int):
        super().__init__(
            name="Health Tea",
            type_=ItemTypes.ITEM_HEALTH_TEA,
            emoji=Emojis.ITEM_HEALTH_TEA,
            owner=owner,
            amount=amount
        )

    async def use(self, inter: disnake.ApplicationCommandInteraction):
        await super().use(inter)


class ItemFactory:
    @staticmethod
    def create_item(item_type: ItemTypes, owner: models.NyahPlayer, amount: int):
        match item_type:
            case ItemTypes.ITEM_CHEST_KEY:
                return PlayerChestItem(owner, amount)
            case ItemTypes.ITEM_TRAIT_SCROLL:
                return PlayerTraitScrollItem(owner, amount)
            case ItemTypes.ITEM_SHONEN_STONE:
                return PlayerShonenStoneItem(owner, amount)
            case ItemTypes.ITEM_HEALTH_TEA:
                return PlayerHealthTeaItem(owner, amount)
            case _:
                raise ValueError(f"Unsupported item type: {item_type}")

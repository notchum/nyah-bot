from collections import deque
from typing import List

import disnake
from disnake.ext import commands

import utils
from bot import NyahBot
from helpers import SuccessEmbed, ErrorEmbed
from utils.constants import Emojis, ItemTypes
from utils.items import ItemFactory, PlayerBaseItem, get_shop_item, SHOP_ITEMS

class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot

    @commands.slash_command()
    async def item(self, inter: disnake.ApplicationCommandInteraction):
        """ Top-level command for items. """
        pass

    @item.sub_command()
    async def shop(self, inter: disnake.ApplicationCommandInteraction):
        """ View the shop! """
        await inter.response.defer()

        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)

        items_str = "\n".join([item.shop_str for item in SHOP_ITEMS])
        embed = disnake.Embed(
            title="ITEM SHOP",
            description=f"Use {utils.slash_command_mention('item buy', 1171329819041083452)} to purchase any item! Balance: `{nyah_player.money:,}` {Emojis.TICKET}\n\n"
                        f"{items_str}",
            color=disnake.Color.og_blurple()
        )

        return await inter.edit_original_response(embed=embed)

    @item.sub_command()
    async def buy(
        self,
        inter: disnake.ApplicationCommandInteraction,
        item: str = commands.Param(choices={x.buy_str: str(x.type.value) for x in SHOP_ITEMS}),
        amount: int = 1
    ):
        """ Buy an item from the shop!
        
            Parameters
            ----------
            item: `ItemTypes`
                The item you want to buy.
            amount: `int`
                The amount of items you want to buy. (Default: 1)
        """
        await inter.response.defer()

        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)

        item_type = ItemTypes(int(item))

        shop_item = get_shop_item(item_type)
        total_price = shop_item.price * amount

        if total_price > nyah_player.money:
            return await inter.edit_original_response(
                embed=ErrorEmbed(
                    description=f"You don't have enough money to buy `{amount}` {shop_item.name}(s)!"
                )
            )

        await nyah_player.add_user_money(-total_price)
        await nyah_player.add_inventory_item(shop_item.type, amount)

        return await inter.edit_original_response(
            embed=SuccessEmbed(
                description=f"You bought `{amount}` {shop_item.name}(s) for `{total_price:,}` {Emojis.TICKET}!"
            )
        )

    @item.sub_command()
    async def use(
        self,
        inter: disnake.ApplicationCommandInteraction,
        item: str
    ):
        """ Use an item from your inventory!
        
            Parameters
            ----------
            item: `str`
                The item you want to use.
        """
        try:
            selected_item_type = ItemTypes(int(item.split(".")[0]))
        except:
            return await inter.response.send_message(
                embed=ErrorEmbed(f"`{item}` is not valid!"),
                ephemeral=True
            )

        await inter.response.defer()

        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)

        for inventory_item in nyah_player.inventory:
            if inventory_item.type != selected_item_type:
                continue
            
            if inventory_item.amount == 0:
                return await inter.edit_original_response(
                    embed=ErrorEmbed(f"You don't have `{item}` in your inventory!")
                )
            
            player_item = ItemFactory.create_item(inventory_item.type, nyah_player, inventory_item.amount)
            await player_item.use(inter)
            return
        
        return await inter.edit_original_response(
            embed=ErrorEmbed(f"TODO: Error message\n{nyah_player.inventory}")
        )

    @use.autocomplete("item")
    async def inventory_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> List[str]:
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)
        if len(nyah_player.inventory) == 0:
            return [f"Your inventory is empty!"]

        player_inventory: List[PlayerBaseItem] = []
        for inv_item in nyah_player.inventory:
            if inv_item.amount == 0:
                continue
            item = ItemFactory.create_item(inv_item.type, nyah_player, inv_item.amount)
            player_inventory.append(item)
        if len(player_inventory) == 0:
            return [f"Your inventory is empty!"]

        return deque([f"{i.type.value}. {i.emoji} {i.name} (x{i.amount})" for i in player_inventory], maxlen=25)


def setup(bot: commands.Bot):
    bot.add_cog(Shop(bot))

import os
import copy
import logging
from typing import List

import disnake
from google_images_search import GoogleImagesSearch

from models import Claim, Waifu, NyahGuild
from helpers import Mongo
from utils import Emojis
from views import WaifuSwapView, WaifuImageSelectView
import utils.utilities as utils

logger = logging.getLogger("nyahbot")
mongo = Mongo()

class WaifuMenuView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, embeds: List[disnake.Embed], author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.embeds = embeds
        self.original_author = author
        
        self.gis = GoogleImagesSearch(os.environ["GOOGLE_KEY"], os.environ["GOOGLE_SEARCH_ID"])
        self.embed_index = 0
        self.prev_page.disabled = True
        if len(self.embeds) == 1:
            self.next_page.disabled = True
            self.swap.disabled = True
        else:
            self.next_page.disabled = False
            self.swap.disabled = False

        # Sets the footer of the embeds with their respective page numbers.
        for i, embed in enumerate(self.embeds, 1):
            embed.set_footer(text=f"{embed.footer.text}  •  {i}/{len(self.embeds)}")
    
    async def on_timeout(self) -> None:
        for child in self.children:
            if isinstance(child, disnake.ui.Button):
                child.disabled = True
        self.title.label = "Menu Timeout"
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

    @disnake.ui.button(emoji=Emojis.PREV_PAGE)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index -= 1
        embed = self.embeds[self.embed_index]
        self.next_page.disabled = False
        if self.embed_index == 0:
            self.prev_page.disabled = True
        if embed.color == disnake.Color.blue():
            self.swap.disabled = True
        else:
            self.swap.disabled = False

        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji=Emojis.NEXT_PAGE)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index += 1
        embed = self.embeds[self.embed_index]
        self.prev_page.disabled = False
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        if embed.color == disnake.Color.blue():
            self.swap.disabled = True
        else:
            self.swap.disabled = False
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @disnake.ui.button(label="Main Menu", style=disnake.ButtonStyle.primary, disabled=True)
    async def title(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        pass
    
    @disnake.ui.button(label="Sell", emoji=Emojis.COINS, row=1)
    async def sell(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        uuid = utils.extract_uuid(current_embed.footer.text)

        claim = await mongo.fetch_claim(uuid)
        waifu = await mongo.fetch_waifu(claim.slug)
        nyah_player = await mongo.fetch_nyah_player(inter.author)

        # update the sold waifu in the db
        await nyah_player.sell_waifu(claim)
        logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                    f"{inter.channel.name}[{inter.channel.id}] | "
                    f"{inter.author}[{inter.author.id}] | "
                    f"Sold {claim.slug}[{claim.id}]")
        
        # remove the embed of the sold waifu
        del self.embeds[self.embed_index]

        # grab the first inactive waifu and make it active if the user just sold an active waifu
        # red_embeds_count = sum(1 for embed in self.embeds if embed.color == disnake.Color.red())
        # if current_embed.color == disnake.Color.green() and red_embeds_count > 0:
        #     for i, e in enumerate(self.embeds):
        #         if e.color == disnake.Color.red():
        #             new_active_embed = e
        #             new_active_embed.color = disnake.Color.green()
        #             self.embeds.insert(nyah_guild.waifu_max_marriages - 1, self.embeds.pop(i))
        #             break
            
            # update the new active waifu's claim
            # uuid = extract_uuid(new_active_embed.footer.text)
            # result = r.db("waifus") \
            #             .table("claims") \
            #             .get(uuid) \
            #             .run(conn)
            # claim = Claim(**result)
            # claim.state = WaifuState.ACTIVE.name
            # r.db("waifus") \
            #     .table("claims") \
            #     .get(uuid) \
            #     .update(claim.__dict__) \
            #     .run(conn)
        
        # reindex the database harem
        harem = await mongo.fetch_harem(inter.author)
        await harem.reindex()
        
        # fix page numbers
        for i in range(len(self.embeds)):
            clean_footer = "  •  ".join(self.embeds[i].footer.text.split("  •  ")[:-1])
            self.embeds[i].set_footer(text=f"{clean_footer}  •  {i+1}/{len(self.embeds)}")
        
        # adjust index
        if self.embed_index == len(self.embeds):
            self.embed_index -= 1
        
        # disable swap if there is only one left
        if len(self.embeds) == 1:
            self.swap.disabled = True

        # disable navigation buttons if needed
        if self.embed_index == 0:
            self.prev_page.disabled = True
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        
        sold_message = f"Sold **__{waifu.name}__** for {claim.price_str}"
        if len(self.embeds) == 0:
            return await inter.response.edit_message(
                content=sold_message,
                view=None
            )
        await inter.response.edit_message(
            content=sold_message,
            embed=self.embeds[self.embed_index],
            view=self
        )
    
    @disnake.ui.button(label="Image", emoji="📸", row=1)
    async def select_image(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        uuid = utils.extract_uuid(current_embed.footer.text)
        
        claim = await mongo.fetch_claim(uuid)
        waifu = await mongo.fetch_waifu(claim.slug)

        if not claim.cached_images_urls:
            # search for 3 extra images
            search_params = {
                "q": f"{waifu.name} {waifu.series[0]}",
                "num": 3,
                "fileType": "jpg|gif|png"
            }
            self.gis.search(search_params)

            # store the images in db
            claim.cached_images_urls = [image.url for image in self.gis.results()]
            await mongo.update_claim(claim)
            logger.info(f"{interaction.guild.name}[{interaction.guild.id}] | "
                        f"{interaction.channel.name}[{interaction.channel.id}] | "
                        f"{interaction.author}[{interaction.author.id}] | "
                        f"Images cached for {claim.slug}[{claim.id}]: {claim.cached_images_urls} ")
        
        # get embed with original image
        embed = copy.deepcopy(current_embed)
        embed.set_image(url=waifu.image_url)
        
        # create embeds with each image
        im_embeds = [embed]
        for image_url in claim.cached_images_urls:
            e = copy.deepcopy(current_embed)
            e.set_image(url=image_url)
            im_embeds.append(e)

        await interaction.response.edit_message(
            embed=im_embeds[0],
            view=WaifuImageSelectView(
                embeds=im_embeds,
                claim=claim,
                author=self.original_author,
                reference_view=self
            )
        )
    
    @disnake.ui.button(label="Swap", emoji=Emojis.SWAP, row=1)
    async def swap(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        selected_name = current_embed.title

        await interaction.response.edit_message(
            content=f"⚠️ **Replacing __{selected_name}__** ⚠️",
            view=WaifuSwapView(
                embeds=self.embeds,
                embed_index=self.embed_index,
                author=self.original_author,
                reference_view=self
            )
        )
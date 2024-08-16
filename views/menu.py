import os
import copy
from typing import List

import disnake
from google_images_search import GoogleImagesSearch
from loguru import logger

import models
import utils
from helpers import Mongo, SuccessEmbed, ErrorEmbed
from utils.constants import Emojis

mongo = Mongo()

class WaifuMenuView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, embeds: List[disnake.Embed], author: disnake.User | disnake.Member) -> None:
        super().__init__()
        self.embeds = embeds
        self.author = author
        
        self.gis = GoogleImagesSearch(os.environ["GOOGLE_KEY"], os.environ["GOOGLE_SEARCH_ID"])
        self.embed_index = 0
        self.prev_page.disabled = True
        if len(self.embeds) == 1:
            self.next_page.disabled = True
        else:
            self.next_page.disabled = False
        
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
        return interaction.author.id == self.author.id

    async def initialize(self):
        await self.set_marry_divorce_button()

    async def set_marry_divorce_button(self):
        current_embed = self.embeds[self.embed_index]
        
        if current_embed.color == disnake.Color.green():
            self.marry_or_divorce.label = "Divorce"
            self.marry_or_divorce.emoji = Emojis.STATE_UNMARRIED
            self.marry_or_divorce.disabled = False
        elif current_embed.color == disnake.Color.red():
            nyah_config = await mongo.fetch_nyah_config()
            num_marriages = await mongo.fetch_harem_married_count(self.author)

            if num_marriages >= nyah_config.waifu_max_marriages:
                self.marry_or_divorce.disabled = True
            else:
                self.marry_or_divorce.disabled = False

            self.marry_or_divorce.label = "Marry"
            self.marry_or_divorce.emoji = Emojis.STATE_MARRIED
        elif current_embed.color == disnake.Color.blue():
            self.marry_or_divorce.disabled = True

    @disnake.ui.button(emoji=Emojis.PREV_PAGE)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index -= 1
        current_embed = self.embeds[self.embed_index]
        
        self.next_page.disabled = False
        if self.embed_index == 0:
            self.prev_page.disabled = True
        
        await self.set_marry_divorce_button()

        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(emoji=Emojis.NEXT_PAGE)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index += 1
        current_embed = self.embeds[self.embed_index]
        
        self.prev_page.disabled = False
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        
        await self.set_marry_divorce_button()
        
        await interaction.response.edit_message(embed=current_embed, view=self)
    
    @disnake.ui.button(label="Main Menu", style=disnake.ButtonStyle.primary, disabled=True)
    async def title(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        pass
    
    @disnake.ui.button(emoji="✖️", style=disnake.ButtonStyle.red)
    async def exit(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        self.stop()
        await inter.response.edit_message(view=None)

    @disnake.ui.button(row=1)
    async def marry_or_divorce(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        uuid = utils.extract_uuid(current_embed.footer.text)
        
        claim = await mongo.fetch_claim(uuid)
        waifu = await mongo.fetch_waifu(claim.slug)
        
        match self.marry_or_divorce.label:
            case "Marry":
            # self.marry_or_divorce.label = "Divorce"
            # self.marry_or_divorce.emoji = Emojis.STATE_UNMARRIED
            # self.marry_or_divorce.disabled = False
            # current_embed.color = disnake.Color.red()
            # current_embed.set_field_at(3, name="Status", value="💔 Unmarried")
            # await interaction.response.edit_message(embed=current_embed, view=self)
            # return
                embed = disnake.Embed(
                    description=f"Are you sure you want to marry **__{waifu.name}__**?",
                    color=disnake.Color.greyple()
                )
            case "Divorce":
                embed = disnake.Embed(
                    description=f"Are you sure you want to divorce **__{waifu.name}__**?",
                    color=disnake.Color.greyple()
                )
            case _:
                logger.error(f"Invalid type: {self.type}")
        
        await interaction.response.edit_message(
            embeds=[current_embed, embed],
            view=MarryDivorceView(
                claim=claim,
                embed=current_embed,
                author=self.author, 
                reference_view=self
            )
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
                "q": f"{waifu.name} {waifu.series[0] if waifu.series else ''}",
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
                author=self.author,
                reference_view=self
            )
        )
    
    @disnake.ui.button(label="Sell", emoji=Emojis.COINS, row=1)
    async def sell(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        uuid = utils.extract_uuid(current_embed.footer.text)

        claim = await mongo.fetch_claim(uuid)
        waifu = await mongo.fetch_waifu(claim.slug)
        nyah_player = await mongo.fetch_nyah_player(inter.author)

        # update the sold waifu in the db
        await nyah_player.sell_waifu(claim)

        # reindex the database harem
        harem = await mongo.fetch_harem(inter.author)
        await harem.reindex()
        
        # create the sold embed
        sold_embed = disnake.Embed(
            description=f"Sold **__{waifu.name}__** for {claim.price_str}",
            color=disnake.Color.gold()
        )

        # remove the embed of the sold waifu
        del self.embeds[self.embed_index]
        
        # remove the view if there are no more embeds
        if len(self.embeds) == 0:
            return await inter.response.edit_message(
                embeds=[current_embed, sold_embed],
                view=None
            )
        
        # fix page numbers
        for i in range(len(self.embeds)):
            clean_footer = "  •  ".join(self.embeds[i].footer.text.split("  •  ")[:-1])
            self.embeds[i].set_footer(text=f"{clean_footer}  •  {i+1}/{len(self.embeds)}")
        
        # adjust index
        if self.embed_index == len(self.embeds):
            self.embed_index -= 1
        
        # update the marry/divorce button
        await self.set_marry_divorce_button()

        # disable navigation buttons if needed
        if self.embed_index == 0:
            self.prev_page.disabled = True
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        
        # update the message
        await inter.response.edit_message(
            embeds=[self.embeds[self.embed_index], sold_embed],
            view=self
        )

        logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                    f"{inter.channel.name}[{inter.channel.id}] | "
                    f"{inter.author}[{inter.author.id}] | "
                    f"Sold {claim.slug}[{claim.id}]")


class WaifuImageSelectView(disnake.ui.View):
    def __init__(self, embeds: List[disnake.Embed], claim: models.Claim, author: disnake.User | disnake.Member, reference_view: disnake.ui.View) -> None:
        super().__init__()
        self.embeds = embeds
        self.claim = claim
        self.author = author
        self.reference_view = reference_view

        self.embed_index = 0
        self.prev_page.disabled = True
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(emoji=Emojis.PREV_PAGE)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index -= 1
        current_embed = self.embeds[self.embed_index]

        self.next_page.disabled = False
        if self.embed_index == 0:
            self.prev_page.disabled = True
        
        self.title.label = f"Image {self.embed_index+1} of 4"
        
        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(emoji=Emojis.NEXT_PAGE)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index += 1
        current_embed = self.embeds[self.embed_index]

        self.prev_page.disabled = False
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        
        self.title.label = f"Image {self.embed_index+1} of 4"
        
        await interaction.response.edit_message(embed=current_embed, view=self)

    @disnake.ui.button(label="Image 1 of 4", style=disnake.ButtonStyle.primary, disabled=True)
    async def title(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        pass
    
    @disnake.ui.button(label="Select Image", emoji="✔️", style=disnake.ButtonStyle.green, row=1)
    async def choose_image(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        self.reference_view.embeds[self.reference_view.embed_index] = current_embed
        
        self.claim.image_url = current_embed.image.url
        await mongo.update_claim(self.claim)
        
        waifu = await mongo.fetch_waifu(self.claim.slug)
        
        success_embed = SuccessEmbed(f"Set new image for **__{waifu.name}__**")
        await interaction.response.edit_message(
            embeds=[current_embed, success_embed],
            view=self.reference_view
        )
    
        logger.info(f"{interaction.guild.name}[{interaction.guild.id}] | "
                    f"{interaction.channel.name}[{interaction.channel.id}] | "
                    f"{interaction.author}[{interaction.author.id}] | "
                    f"Selected image {current_embed.image.url} for {self.claim.slug}[{self.claim.id}]")
        
    @disnake.ui.button(label="Cancel", emoji="✖️", style=disnake.ButtonStyle.red, row=1)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        for current_embed in reversed(self.embeds):
            if current_embed.image.url == self.claim.image_url:
                break
        
        await interaction.response.edit_message(embed=current_embed, view=self.reference_view)


class MarryDivorceView(disnake.ui.View):
    def __init__(self, claim: models.Claim, embed: disnake.Embed, author: disnake.User | disnake.Member, reference_view: disnake.ui.View) -> None:
        super().__init__()
        self.claim = claim
        self.embed = embed
        self.author = author
        self.reference_view = reference_view

        for child in reference_view.children:
            if isinstance(child, disnake.ui.Button) and child.label in ["Marry", "Divorce"]:
                self.marry_divorce_button = child
                match self.marry_divorce_button.label:
                    case "Marry":
                        self.confirm.label="Confirm Marry?"
                        self.confirm.emoji=Emojis.STATE_MARRIED
                    case "Divorce":
                        self.confirm.label="Confirm Divorce?"
                        self.confirm.emoji=Emojis.STATE_UNMARRIED
                    case _:
                        logger.error(f"Invalid type: {self.type}")

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(emoji=Emojis.PREV_PAGE, disabled=True)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        pass

    @disnake.ui.button(emoji=Emojis.NEXT_PAGE, disabled=True)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        pass

    @disnake.ui.button(label="Marry/Divorce Menu", style=disnake.ButtonStyle.primary, disabled=True)
    async def title(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        pass

    @disnake.ui.button(style=disnake.ButtonStyle.green, row=1)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        match self.marry_divorce_button.label:
            case "Marry":
                self.claim.marry()
                await mongo.update_claim(self.claim)
                
                self.embed.color = disnake.Color.green()
                status_field_index = next((i for i, field in enumerate(self.embed.fields) if field.name == "Status"), None)
                if status_field_index is not None:
                    self.embed.set_field_at(
                        index=status_field_index,
                        name="Status",
                        value=f"{Emojis.STATE_MARRIED} Married"
                    )

                self.marry_divorce_button.label = "Divorce"
                self.marry_divorce_button.emoji = Emojis.STATE_UNMARRIED

                waifu = await mongo.fetch_waifu(self.claim.slug)
                result_embed = disnake.Embed(
                    description=f"Married **__{waifu.name}__** {Emojis.STATE_MARRIED}",
                    color=disnake.Color.fuchsia()
                )
            case "Divorce":
                self.claim.divorce()
                await mongo.update_claim(self.claim)

                self.embed.color = disnake.Color.red()
                status_field_index = next((i for i, field in enumerate(self.embed.fields) if field.name == "Status"), None)
                if status_field_index is not None:
                    self.embed.set_field_at(
                        index=status_field_index,
                        name="Status",
                        value=f"{Emojis.STATE_UNMARRIED} Unmarried"
                    )
                
                self.marry_divorce_button.label = "Marry"
                self.marry_divorce_button.emoji = Emojis.STATE_MARRIED
                
                waifu = await mongo.fetch_waifu(self.claim.slug)
                result_embed = disnake.Embed(
                    description=f"Divorced **__{waifu.name}__** {Emojis.STATE_UNMARRIED}",
                    color=disnake.Color.dark_blue()
                )
            case _:
                logger.error(f"Invalid type: {self.type}")
                error_embed = ErrorEmbed("Something went wrong!")
                return await interaction.response.edit_message(
                    embed=error_embed,
                    view=None
                )
        
        await interaction.response.edit_message(
            embeds=[self.embed, result_embed],
            view=self.reference_view
        )

    @disnake.ui.button(label="Cancel", emoji="✖️", style=disnake.ButtonStyle.red, row=1)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.edit_message(embed=self.embed, view=self.reference_view)

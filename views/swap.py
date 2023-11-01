import copy
import logging
from typing import List

import disnake

from models import Claim
from helpers import Mongo
import utils.utilities as utils

logger = logging.getLogger("nyahbot")
mongo = Mongo()

class WaifuSwapView(disnake.ui.View):
    def __init__(self, embeds: List[disnake.Embed], embed_index: int, author: disnake.User | disnake.Member, reference_view: disnake.ui.View) -> None:
        super().__init__()
        self.embeds = embeds
        self.embed_index = embed_index
        self.original_author = author
        self.reference_view = reference_view
        
        self.selected_index = self.embed_index
        if self.embed_index == 0:
            self.prev_page.disabled = True
        elif self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        self.confirm.disabled = True

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.original_author.id

    @logger.catch
    @disnake.ui.button(emoji="<:leftWaifu:1158460793063477420>", custom_id="prev_page_button",
                        style=disnake.ButtonStyle.secondary)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index -= 1
        current_embed = self.embeds[self.embed_index]
        selected_name = self.embeds[self.selected_index].title

        self.next_page.disabled = False
        if self.embed_index == 0:
            self.prev_page.disabled = True
        
        if self.embed_index == self.selected_index:
            content = f"⚠️ **Replacing `{self.selected_index + 1}` __{selected_name}__**  ⚠️"
            self.confirm.disabled = True
        elif current_embed.color == disnake.Color.blue():
            content = f"❄️ **`{self.embed_index + 1}` __{current_embed.title}__ is currently on cooldown** ❄️"
            self.confirm.disabled = True
        else:
            content = f"❓ **Swap `{self.selected_index + 1}` __{selected_name}__ with `{self.embed_index + 1}` __{current_embed.title}__?**  ❓"
            self.confirm.disabled = False
        
        await interaction.response.edit_message(content=content, embed=current_embed, view=self)

    @logger.catch
    @disnake.ui.button(emoji="<:rightWaifu:1158460837359538186>", custom_id="next_page_button",
                        style=disnake.ButtonStyle.secondary)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        self.embed_index += 1
        current_embed = self.embeds[self.embed_index]
        selected_name = self.embeds[self.selected_index].title

        self.prev_page.disabled = False
        if self.embed_index == len(self.embeds) - 1:
            self.next_page.disabled = True
        
        if self.embed_index == self.selected_index:
            content = f"⚠️ **Replacing `{self.selected_index + 1}` __{selected_name}__** ⚠️"
            self.confirm.disabled = True
        elif current_embed.color == disnake.Color.blue():
            content = f"❄️ **`{self.embed_index + 1}` __{current_embed.title}__ is currently on cooldown** ❄️"
            self.confirm.disabled = True
        else:
            content = f"❓ **Swap `{self.selected_index + 1}` __{selected_name}__ with `{self.embed_index + 1}` __{current_embed.title}__?** ❓"
            self.confirm.disabled = False
        
        await interaction.response.edit_message(content=content, embed=current_embed, view=self)
    
    @disnake.ui.button(label="Swap Menu", custom_id="title_button",
                        style=disnake.ButtonStyle.primary, disabled=True)
    async def title(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        pass
    
    @logger.catch
    @disnake.ui.button(label="Confirm", emoji="✔️", custom_id="confirm_button",
                        style=disnake.ButtonStyle.green, row=1)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        old_embed = self.embeds[self.selected_index]
        new_embed = self.embeds[self.embed_index]
        
        old_uuid = utils.extract_uuid(old_embed.footer.text)
        new_uuid = utils.extract_uuid(new_embed.footer.text)

        old_claim = await mongo.fetch_claim(old_uuid)
        new_claim = await mongo.fetch_claim(new_uuid)

        old_claim_state = old_claim.state
        new_claim_state = new_claim.state

        # insert a copy of the old embed at new index, then delete new embed
        e = copy.deepcopy(old_embed)
        e.color = new_embed.color
        e.set_footer(text=f"{old_claim.id}  •  {self.embed_index + 1}/{len(self.embeds)}")
        self.embeds.insert(self.embed_index, e)
        del self.embeds[self.embed_index + 1]
        old_claim.index = self.embed_index
        old_claim.state = new_claim_state
        await mongo.update_claim(old_claim)

        # insert a copy of the new embed at old index, then delete old embed
        e = copy.deepcopy(new_embed)
        e.color = old_embed.color
        e.set_footer(text=f"{new_claim.id}  •  {self.selected_index + 1}/{len(self.embeds)}")
        self.embeds.insert(self.selected_index, e)
        del self.embeds[self.selected_index + 1]
        new_claim.index = self.selected_index
        new_claim.state = old_claim_state
        await mongo.update_claim(new_claim)

        logger.info(f"{interaction.guild.name}[{interaction.guild.id}] | "
                    f"{interaction.channel.name}[{interaction.channel.id}] | "
                    f"{interaction.author}[{interaction.author.id}] | "
                    f"Swapped {old_claim.slug}({self.selected_index})[{old_claim.id}] "
                    f"with {new_claim.slug}({self.embed_index})[{new_claim.id}]")
        
        self.reference_view.embed_index = self.embed_index
        self.reference_view.next_page.disabled = self.embed_index == len(self.embeds) - 1
        self.reference_view.prev_page.disabled = self.embed_index == 0

        await interaction.response.edit_message(
            content=f"✅ **Swapped __{old_embed.title}__ with __{new_embed.title}__** ✅",
            embed=self.embeds[self.embed_index],
            view=self.reference_view
        )
    
    @disnake.ui.button(label="Cancel", emoji="✖️", custom_id="cancel_button",
                        style=disnake.ButtonStyle.red, row=1)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        current_embed = self.embeds[self.embed_index]
        self.reference_view.embed_index = self.embed_index
        self.reference_view.prev_page.disabled = self.prev_page.disabled
        self.reference_view.next_page.disabled = self.next_page.disabled
        
        await interaction.response.edit_message(
            content=None,
            embed=current_embed,
            view=self.reference_view
        )
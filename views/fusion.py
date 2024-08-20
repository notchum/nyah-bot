import re
import uuid
from typing import List, Dict

import disnake

import models
import utils
from helpers import Mongo, WarningEmbed, WaifuClaimEmbed
from utils.constants import Emojis, WaifuState, Fusions, TIER_EMOJI_MAP, FUSION_TIER_MAP

mongo = Mongo()

class FusionTypeButton(disnake.ui.Button):
    def __init__(self, fusion_type: Fusions, disabled: bool):
        self.fusion_type = fusion_type
        
        label = None
        emoji = None
        row = 0
        if self.fusion_type == Fusions.SILVER:
            label = "SILVER FUSION"
            emoji = Emojis.TIER_SILVER
        elif self.fusion_type == Fusions.GOLD:
            label = "GOLD FUSION"
            emoji = Emojis.TIER_GOLD
        elif self.fusion_type == Fusions.EMERALD:
            label = "EMERALD FUSION"
            emoji = Emojis.TIER_EMERALD
            row = 1
        elif self.fusion_type == Fusions.RUBY:
            label = "RUBY FUSION"
            emoji = Emojis.TIER_RUBY
            row = 1
        elif self.fusion_type == Fusions.DIAMOND:
            label = "DIAMOND FUSION"
            emoji = Emojis.TIER_DIAMOND
            row = 1
        super().__init__(label=label, emoji=emoji, row=row, disabled=disabled)
    
    async def callback(self, inter: disnake.MessageInteraction):
        if isinstance(self.view, FusionStageOneView):
            self.view.selected_fusion_type = self.fusion_type
            self.view.stop()
        return await super().callback(inter)

class FusionStageOneView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, author: disnake.User | disnake.Member, fusion_count_dict: Dict[Fusions, int]):
        super().__init__()
        self.author = author
        self.fusion_count_dict = fusion_count_dict
        self.selected_fusion_type = None

        for fusion, count in fusion_count_dict.items():
            if count == 0:
                disabled = True
            else:
                disabled = False
            
            self.add_item(FusionTypeButton(fusion, disabled))

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)
        await super().on_timeout()


class FusionClaimStringSelect(disnake.ui.StringSelect["FusionStageTwoView"]):
    def __init__(self, fusion_candidates: List[models.Claim]):
        self.fusion_candidates = fusion_candidates
        options = [
            disnake.SelectOption(
                label=claim.name,
                value=str(claim.id),
                emoji=TIER_EMOJI_MAP[claim.tier],
                description=claim.stats_str,
            )
            for claim in fusion_candidates
        ]
        super().__init__(
            placeholder="Select three of your characters",
            min_values=3,
            max_values=3,
            options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        selected_fusions = []
        for uuid_str in self.values:
            selected_claim_id = uuid.UUID(uuid_str)
            for claim in self.fusion_candidates:
                if selected_claim_id == claim.id:
                    selected_fusions.append(claim)

        if len(selected_fusions) != 3:
            return await inter.edit_original_response(
                content="somthing wen wrong",
                view=None
            )

        await self.view.finalize(selected_fusions)

        return await super().callback(inter)


class FusionStageTwoView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, author: disnake.User | disnake.Member, fusion_candidates: List[models.Claim], fusion_type: Fusions):
        super().__init__()
        self.author = author
        self.fusion_candidates = fusion_candidates
        self.fusion_type = fusion_type

        self.fusion_select = FusionClaimStringSelect(self.fusion_candidates)
        self.add_item(self.fusion_select)
        self.confirm.disabled = True

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)
        await super().on_timeout()

    async def select_fusion_claim(self, claim: models.Claim):
        embed = self.message.embeds[0]
        embed.description = re.sub(r'`Waiting for selection...`', claim.name, embed.description, count=1)
        
        self.remove_item(self.fusion_select)
        self.fusion_candidates.remove(claim)
        self.fusion_select = FusionClaimStringSelect(self.fusion_candidates, "Select one of your characters")
        self.add_item(self.fusion_select)

        await self.message.edit(
            embed=embed,
            view=self
        )
    
    async def finalize(self, selected_fusions: List[models.Claim]):
        self.remove_item(self.fusion_select)
        self.selected_fusions = selected_fusions
        
        # find length of longest name
        t = max([len(c.name) for c in selected_fusions])
        e = ["`══╗`", f"`══╬══⇒` `?????` {TIER_EMOJI_MAP[FUSION_TIER_MAP[self.fusion_type]]}", "`══╝`"]
        embed = self.message.embeds[0]
        warning_description = ""
        for claim, endl in zip(selected_fusions, e):
            embed.description += f"\n{TIER_EMOJI_MAP[claim.tier]} `{claim.name :<{t}}` {endl}"
            
            if claim.state == WaifuState.ACTIVE:
                warning_description += f"You are married to **__{claim.name}__**!\n"

        embed.description += f"\n\nSelect **Confirm** {Emojis.CHECK_MARK} to finish fusing."
        embeds = [embed]

        if warning_description:
            warning_description += "\n__Fusing will mean that you lose your marriage. Are you sure?__"
            embeds.append(WarningEmbed(warning_description))

        self.confirm.disabled = False
        await self.message.edit(
            embeds=embeds,
            view=self
        )

    @disnake.ui.button(label="Confirm", emoji=Emojis.CHECK_MARK, style=disnake.ButtonStyle.green, row=1)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        # get a random character that is a tier higher
        total_characters = await mongo.fetch_waifu_count()
        rank_range = utils.rank_from_tier(total_characters, FUSION_TIER_MAP[self.fusion_type])
        range_aggregation = {"$match": {"popularity_rank": {"$gte": rank_range.start, "$lte": rank_range.stop}}}
        new_waifu = await mongo.fetch_random_waifu([range_aggregation])
        
        # crate a claim from that character
        nyah_player = await mongo.fetch_nyah_player(interaction.author)
        new_claim = await nyah_player.generate_claim(new_waifu)
        new_claim.guild_id=interaction.guild.id
        new_claim.channel_id=interaction.channel.id
        new_claim.message_id=interaction.message.id
        new_claim.jump_url=interaction.message.jump_url
        new_claim.timestamp=interaction.created_at
        await mongo.insert_claim(new_claim)
        
        # remove each fused claim from the user's harem
        for claim in self.selected_fusions:
            claim.state = WaifuState.FUSED
            claim.index = None
            await claim.save()
        
        # reindex the user's harem
        harem = await mongo.fetch_harem(interaction.author)
        await harem.reindex()
        
        # edit message with the new claim
        embed = interaction.message.embeds[0]
        embed.description = embed.description.replace("?????", new_claim.name)
        claim_embed = WaifuClaimEmbed(new_waifu, new_claim)
        await interaction.response.edit_message(
            embeds=[embed, claim_embed],
            view=None
        )
        self.stop()
    
    @disnake.ui.button(label="Cancel", emoji=Emojis.CROSS_MARK, style=disnake.ButtonStyle.red, row=1)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        embed = disnake.Embed(
            description="Cancelled",
            color=disnake.Color.red()
        )
        await interaction.response.edit_message(
            embeds=[interaction.message.embeds[0], embed],
            view=None
        )
        self.stop()



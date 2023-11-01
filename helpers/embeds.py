import datetime

import disnake
from loguru import logger

from nyahbot.util.constants import (
    Emojis,
    WaifuState,
    Experience,
    Money,
    Cooldowns,
)
from nyahbot.util.dataclasses import (
    Waifu,
    Claim,
)
from nyahbot.util import (
    reql_helpers,
    api_helpers,
)


class SuccessEmbed(disnake.Embed):
    def __init__(self, description: str = None):
        super().__init__(
            title="Success! ✅",
            description=description,
            color=disnake.Color.green()
        )

class ErrorEmbed(disnake.Embed):
    def __init__(self, description: str = None):
        super().__init__(
            title="Error! 💢",
            description=description,
            color=disnake.Color.red()
        )

async def get_waifu_base_embed(waifu: Waifu) -> disnake.Embed:
    """ Get a bare-bones embed for a waifu.
        - Name
        - Husbando classification
        - Default Image
        - Series (with MAL links)

    """
    # Get links to series on MAL
    waifu_series = []
    for series in waifu.series:
        mal_url = await api_helpers.search_mal_series(series)
        if mal_url:
            waifu_series.append(f"[{series}]({mal_url})")
        else:
            waifu_series.append(series)
    waifu_series = "\n".join(waifu_series)
    
    embed = disnake.Embed(
        title=waifu.name + "  ♂️" if waifu.husbando else waifu.name + "  ♀️",
        url=waifu.url,
        color=disnake.Color.fuchsia()
    ) \
    .set_image(url=waifu.image_url) \
    .add_field(name="Appears In", value=waifu_series)

    return embed

async def get_waifu_core_embed(waifu: Waifu) -> disnake.Embed:
    """ Get an ultra-detailed embed for a waifu.
        - Alternate names
        - Age & DOB
        - Measurements
        - Origin
        
    """
    embed = await get_waifu_base_embed(waifu)
    embed.description = (waifu.description[:4092] + "...") if len(waifu.description) > 4092 else waifu.description
    embed.color = disnake.Color.teal()
    embed.add_field(name="Original Name", value=waifu.original_name if waifu.original_name else "-") \
         .add_field(name="Romaji Name", value=waifu.romaji_name if waifu.romaji_name else "-") \
         .add_field(name="Place of Origin", value=waifu.origin if waifu.origin else "-") \
         .add_field(name="Age", value=waifu.age if waifu.age else "-") \
         .add_field(name="Date of Birth", value=waifu.date_of_birth if waifu.date_of_birth else "-") \
         .add_field(name="Height", value=waifu.height if waifu.height else "-") \
         .add_field(name="Weight", value=waifu.weight if waifu.weight else "-") \
         .add_field(name="Blood Type", value=waifu.blood_type if waifu.blood_type else "-") \
         .add_field(name="Bust", value=waifu.bust if waifu.bust else "-") \
         .add_field(name="Waist", value=waifu.waist if waifu.waist else "-") \
         .add_field(name="Hip", value=waifu.hip if waifu.hip else "-")
    return embed

async def get_waifu_skills_embed(claim: Claim) -> disnake.Embed:
    waifu = await reql_helpers.get_waifu_core(claim.slug)
    
    embed = await get_waifu_base_embed(waifu)
    embed.add_field(name="Price", value=claim.price_str)
    embed.add_field(name="Traits", value=claim.trait_str)
    embed.add_field(name=f"Skills ({claim.stats_str})", value=claim.still_str)
    embed.set_footer(text=claim.id)
    embed.set_image(url=claim.image_url)
    return embed

async def get_waifu_claim_embed(claim: Claim, owner: disnake.User | disnake.Member) -> disnake.Embed:
    """ Get an embed of a waifu just claimed.
        - Price listed.
        - Skills listed.
        - Traits listed.

        Parameters
        ----------
        waifu: `Waifu`
            The waifu to retrieve.
        owner: `disnake.User` | `disnake.Member`
            The owner of this waifu.
        
        Returns
        -------
        `disnake.Embed`
            The embed.
    """
    waifu = await reql_helpers.get_waifu_core(claim.slug)
    waifu_type = "husbando" if waifu.husbando else "waifu"

    embed = await get_waifu_skills_embed(claim)
    embed.timestamp = disnake.utils.utcnow()
    embed.set_footer(text=f"A {waifu_type} for {owner.name} >.<")
    return embed

async def get_waifu_harem_embed(claim: Claim) -> disnake.Embed:
    """ Get an embed of a waifu in a harem.
        - Embed color represents state.
        - Skills listed.
        - Price listed.
        - Traits listed.
        - Marriage status.
    
    """
    if claim.state == WaifuState.ACTIVE.name:
        color = disnake.Color.green()
        status = f"💕 Married"
    elif claim.state == WaifuState.COOLDOWN.name:
        color = disnake.Color.blue()
        status = f"❄️ Cooldown"
    elif claim.state == WaifuState.INACTIVE.name:
        color = disnake.Color.red()
        status = f"💔 Unmarried"
    
    embed = await get_waifu_skills_embed(claim)
    embed.add_field(name="Status", value=status)
    embed.color = color
    return embed

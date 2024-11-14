import disnake

import models
from helpers import Mongo
from utils.constants import TIER_COLOR_MAP, TIER_TITLE_MAP, WAIFUSTATE_TITLE_MAP

mongo = Mongo()

# fmt: off
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


class WarningEmbed(disnake.Embed):
    def __init__(self, description: str = None):
        super().__init__(
            title="Warning! ⚠️",
            description=description,
            color=disnake.Color.orange()
        )


class WaifuBaseEmbed(disnake.Embed):
    """Get a bare-bones embed for a waifu.
        - Name
        - Husbando classification
        - Default Image
        - Series (with MAL links)
    """
    def __init__(self, waifu: models.Waifu):
        super().__init__(
            title=waifu.name + "  ♂️" if waifu.husbando else waifu.name + "  ♀️",
            url=waifu.url,
            color=disnake.Color.fuchsia()
        )
        self.set_image(url=waifu.image_url)
        self.add_field(name="Appears In", value="\n".join(waifu.series))
    
    @classmethod
    async def create(cls, waifu: models.Waifu):
        self = WaifuBaseEmbed()
        # waifu_series = []
        # for series in waifu.series:
        #     mal_url = await api_helpers.search_mal_series(series)
        #     if mal_url:
        #         waifu_series.append(f"[{series}]({mal_url})")
        #     else:
        #         waifu_series.append(series)
        # waifu_series = "\n".join(waifu_series)
        
        # embed = disnake.Embed(
        #     title=waifu.name + "  ♂️" if waifu.husbando else waifu.name + "  ♀️",
        #     url=waifu.url,
        #     color=disnake.Color.fuchsia()
        # ) \
        # .set_image(url=waifu.image_url) \
        # .add_field(name="Appears In", value=waifu_series)

        return self


class WaifuCoreEmbed(WaifuBaseEmbed):
    """Get an ultra-detailed embed for a waifu.
        - Alternate names
        - Age & DOB
        - Measurements
        - Origin
    """
    def __init__(self, waifu: models.Waifu):
        super().__init__(waifu)
        self.description = (waifu.description[:4092] + "...") if len(waifu.description) > 4092 else waifu.description
        self.color = disnake.Color.teal()
        self.add_field(name="Original Name", value=waifu.original_name if waifu.original_name else "-") \
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


class WaifuClaimEmbed(WaifuBaseEmbed):
    """Get an embed of a claimed waifu.
        - Tier
        - Skill Value
        - Marriage status
    """
    def __init__(self, waifu: models.Waifu, claim: models.Claim):
        super().__init__(waifu)
        self.color = TIER_COLOR_MAP[claim.tier]
        self.add_field(name="Tier", value=TIER_TITLE_MAP[claim.tier], inline=False) \
            .add_field(name="Skill Points", value=claim.skill_str_short, inline=False) \
            .add_field(name="Status", value=WAIFUSTATE_TITLE_MAP[claim.state], inline=False)
        self.set_footer(text=claim.id)
        self.set_image(url=claim.image_url)


class WaifuHaremEmbed(WaifuBaseEmbed):
    """Get an embed of a claimed waifu.
        - Price listed.
        - Skills listed.
        - Traits listed.
        - Tier.
        - Marriage status.
    """
    def __init__(self, waifu: models.Waifu, claim: models.Claim):
        super().__init__(waifu)
        self.color = TIER_COLOR_MAP[claim.tier]
        self.add_field(name="Tier", value=TIER_TITLE_MAP[claim.tier]) \
            .add_field(name="Trait", value=claim.trait_str) \
            .add_field(name=f"Skills ({claim.skill_str_short})", value=claim.skill_str_long) \
            .add_field(name="Status", value=WAIFUSTATE_TITLE_MAP[claim.state])
        self.set_footer(text=claim.id)
        self.set_image(url=claim.image_url)
# fmt: on

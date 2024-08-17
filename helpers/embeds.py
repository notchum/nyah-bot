import disnake

import models
from helpers import Mongo
from utils.constants import WaifuState

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
        - Price listed.
        - Skills listed.
        - Traits listed.
    """
    def __init__(self, waifu: models.Waifu, claim: models.Claim):
        super().__init__(waifu)
        self.add_field(name="Price", value=claim.price_str) \
            .add_field(name="Traits", value=claim.trait_str) \
            .add_field(name=f"Skills ({claim.stats_str})", value=claim.skill_str)
        self.set_footer(text=claim.id)
        self.set_image(url=claim.image_url)


class WaifuHaremEmbed(WaifuClaimEmbed):
    """Get an embed of a waifu in a harem.
        - Embed color represents state.
        - Skills listed.
        - Price listed.
        - Traits listed.
        - Marriage status.
    """
    def __init__(self, waifu: models.Waifu, claim: models.Claim):
        if claim.state == WaifuState.ACTIVE.value:
            color = disnake.Color.green()
            status = f"💕 Married"
        elif claim.state == WaifuState.COOLDOWN.value:
            color = disnake.Color.blue()
            status = f"❄️ Cooldown"
        elif claim.state == WaifuState.INACTIVE.value:
            color = disnake.Color.red()
            status = f"💔 Unmarried"
        
        super().__init__(waifu, claim)
        self.add_field(name="Status", value=status)
        self.color = color
# fmt: on

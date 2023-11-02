import datetime

import disnake

from models import Waifu, Claim
from helpers import Mongo
from utils import WaifuState

mongo = Mongo()

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
    @classmethod
    async def create(cls, waifu: Waifu):
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

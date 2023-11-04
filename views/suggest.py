import disnake

from models import Waifu
from helpers import SuccessEmbed, ErrorEmbed
import utils.utilities as utils

class SuggestionModal(disnake.ui.Modal):
    def __init__(self) -> None:
        components = [
            disnake.ui.TextInput(
                label="Name",
                placeholder="The name of the character",
                custom_id="name",
                style=disnake.TextInputStyle.short,
                min_length=5,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label="Series",
                placeholder="The series the character is from",
                custom_id="series",
                style=disnake.TextInputStyle.short,
                min_length=5,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label="Description",
                placeholder="The description of the character",
                custom_id="description",
                style=disnake.TextInputStyle.paragraph,
                min_length=5,
                max_length=1024,
            ),
            disnake.ui.TextInput(
                label="Image URL",
                placeholder="The image URL of the character",
                custom_id="image_url",
                style=disnake.TextInputStyle.short,
                min_length=5,
                max_length=1024,
            ),
        ]
        super().__init__(title="Character Suggestion", custom_id="character_suggest", components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        suggestion_name = inter.text_values["name"]
        suggestion_series = inter.text_values["series"]
        suggestion_description = inter.text_values["description"]
        suggestion_image_url = inter.text_values["image_url"]

        slug = utils.slugify(f"{suggestion_name} {suggestion_series}")
        waifu = Waifu(
            slug=slug,
            url="https://nyah.moe/character/{slug}",
            source="custom",
            husbando=False,
            name=suggestion_name,
            series=[suggestion_series],
            description=suggestion_description,
            image_url=suggestion_image_url,
            tags=["custom"]
        )

        suggestion_embed = disnake.Embed(
            title=suggestion_name,
            description=suggestion_description,
            color=disnake.Color.blurple(),
        )
        suggestion_embed.add_field(name="Series", value=suggestion_series)
        suggestion_embed.set_image(url=suggestion_image_url)

        confirm_embed = SuccessEmbed(f"Your suggestion has been submitted. Thank you for your contribution!\n"
                                     f"**__Submitted at:__** {utils.get_dyn_date_long_time_long(inter.created_at)}")
        
        await inter.response.send_message(embeds=[suggestion_embed, confirm_embed])

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.response.send_message("Oops, something went wrong.", ephemeral=True)

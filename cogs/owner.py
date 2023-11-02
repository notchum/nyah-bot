import codecs

import disnake
from disnake.ext import commands

from bot import NyahBot
from helpers import SuccessEmbed, ErrorEmbed

class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot

    ##*************************************************##
    ##********           ABSTRACTIONS           *******##
    ##*************************************************##

    ##*************************************************##
    ##********              EVENTS              *******##
    ##*************************************************##

    ##*************************************************##
    ##********              TASKS               *******##
    ##*************************************************##

    ##*************************************************##
    ##********             COMMANDS             *******##
    ##*************************************************##

    @commands.is_owner()
    @commands.slash_command(guild_ids=[776929597567795247, 759514108625682473])
    async def owner(self, inter: disnake.ApplicationCommandInteraction):
        """ Top-level command group for admin commands. """
        pass

    @owner.sub_command()
    async def say(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel,
        text: str
    ):
        """ Make the bot say whatever you want.

            Parameters
            ----------
            channel: `disnake.TextChannel`
                The channel where the message will be sent.
            text: `str`
                What the bot will say.
        """
        await self.bot.get_channel(channel.id).send(codecs.decode(text, "unicode_escape"))
        return await inter.response.send_message(
            embed=SuccessEmbed(),
            ephemeral=True
        )

    @owner.sub_command()
    async def change_avatar(
        self,
        inter: disnake.ApplicationCommandInteraction,
        image: disnake.Attachment = None,
        image_url: str = None
    ):
        """ Change the bot's avatar.

            Parameters
            ----------
            image: `disnake.Attachment`
                The new avatar (as an attached image file).
            image_url: `str`
                The new avatar (as a link to an image).
        """
        if image_url == None and image:
            if 'image/' not in image.content_type:
                return await inter.response.send_message("Attachment isn't an image!")
            avatar_url = image.url
        else:
            avatar_url = image_url.strip("<>") if image_url else None

        try:
            async with self.bot.session.get(url=avatar_url) as response:
                if response.status != 200:
                    return await inter.response.send_message(
                        embed=ErrorEmbed(f"That avatar URL returned status code `{response.status}`")
                    )
                av = response.content
                await self.bot.user.edit(avatar=av)
                return await inter.response.send_message(f"Successfully changed the avatar to:\n{avatar_url}")
        except disnake.HTTPException as err:
            return await inter.response.send_message(embed=ErrorEmbed(f"{err}"), ephemeral=True)

    @owner.sub_command()
    async def download_log(self, inter: disnake.ApplicationCommandInteraction):
        """ Download the current log file. """
        return await inter.response.send_message(file=disnake.File("log/nyah-bot.log"), ephemeral=True)

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(Owner(bot))
import codecs
import asyncio

import disnake
from disnake.ext import commands

from bot import NyahBot
from nyahbot.util import utilities

class Admin(commands.Cog):
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

    @commands.slash_command(default_member_permissions=disnake.Permissions(administrator=True))
    async def admin(self, inter: disnake.ApplicationCommandInteraction):
        """ Top-level command group for admin commands. """
        pass

    @admin.sub_command()
    async def setup(self, inter: disnake.ApplicationCommandInteraction):
        """ Configure and bind server channels. """
        channel_custom_ids = ['general_channel_id', 'bot_log_channel_id', 'meme_channel_id', 'waifu_war_channel_id']
        channels = r.db("discord").table("guilds").get(str(inter.guild.id)).pluck(channel_custom_ids).run(conn)
        components = []
        for custom_id, channel_id in channels.items():
            components.append(
                disnake.ui.TextInput(
                    label=' '.join(custom_id.split('_')[:-1]).title(),
                    placeholder="Put either the channel name EXACTLY or the channel ID",
                    value=f"{inter.guild.system_channel.name}" if not channel_id else self.bot.get_channel(int(channel_id)).name,
                    custom_id=custom_id,
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    max_length=50,
                )
            )
        await inter.response.send_modal(
            title="Nyah setup",
            custom_id="setup_bind",
            components=components
        )
        try:
            modal_inter: disnake.ModalInteraction = await self.bot.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "setup_bind" and i.author.id == inter.author.id,
                timeout=300
            )
        except asyncio.TimeoutError:
            # The user didn't submit the modal in the specified period of time.
            # This is done since Discord doesn't dispatch any event for when a modal is closed/dismissed.
            return
        embed = disnake.Embed(
            title=f"{inter.guild.name} Config",
            color=disnake.Color.blue()
        )
        description = ""
        for custom_id, value in modal_inter.text_values.items():
            if value.isdigit(): bind_channel = self.bot.get_channel(int(value))
            else: bind_channel = disnake.utils.get(inter.guild.text_channels, name=value)

            if not bind_channel:
                logger.error(f"{inter.guild.name}[{inter.guild.id}] | Couldn't bind channel {value}!")
                continue

            r.db("discord").table("guilds").get(str(inter.guild.id)).update({custom_id: str(bind_channel.id)}).run(conn)
            logger.info(f"{inter.guild.name}[{inter.guild.id}] | Binded channel {bind_channel.name}[{bind_channel.id}] to {custom_id}")
            clean_channel_role = ' '.join(custom_id.split('_')[:-1]).title()
            description += f"{clean_channel_role}: {bind_channel.mention} [{bind_channel.id}]\n"
        r.db("discord").table("guilds").get(str(inter.guild.id)).update({"setup_finished": True}).run(conn)
        embed.description = description
        return await modal_inter.response.send_message(embed=embed, ephemeral=True)

    @admin.sub_command()
    async def config(self, inter: disnake.ApplicationCommandInteraction):
        """ View the server config and binded channels. """
        embed = disnake.Embed(
            title=f"{inter.guild.name} Config",
            color=disnake.Color.blue()
        )
        description = ""
        channel_custom_ids = ['general_channel_id', 'bot_log_channel_id', 'meme_channel_id', 'waifu_war_channel_id']
        channels = r.db("discord").table("guilds").get(str(inter.guild.id)).pluck(channel_custom_ids).run(conn)
        for custom_id, channel_id in channels.items():
            clean_channel_role = ' '.join(custom_id.split('_')[:-1]).title()
            if not channel_id:
                description += f"{clean_channel_role}: Not binded! Use `/setup` to bind a channel."
                continue
            channel = self.bot.get_channel(int(channel_id))
            description += f"{clean_channel_role}: {channel.mention} [{channel.id}]\n"
        if not description:
            return await inter.response.send_message(embed=utilities.get_error_embed("No channels binded! Use `/setup` to get started."), ephemeral=True)
        embed.description = description
        return await inter.response.send_message(embed=embed, ephemeral=True)

    @admin.sub_command()
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
            embed=utilities.get_success_embed(""),
            ephemeral=True
        )

    @admin.sub_command()
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
            async with session.get(url=avatar_url) as response:
                if response.status != 200:
                    return await inter.response.send_message(
                        embed=utilities.get_error_embed(f"That avatar URL returned status code `{response.status}`")
                    )
                av = response.content
                await self.bot.user.edit(avatar=av)
                return await inter.response.send_message(f"Successfully changed the avatar to:\n{avatar_url}")
        except disnake.HTTPException as err:
            return await inter.response.send_message(embed=utilities.get_error_embed(f"{err}"), ephemeral=True)

    @admin.sub_command()
    async def download_log(self, inter: disnake.ApplicationCommandInteraction):
        """ Download the current log file. """
        return await inter.response.send_message(file=disnake.File("log/nyah-bot.log"), ephemeral=True)

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
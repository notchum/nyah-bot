import disnake
from disnake.ext import commands
from loguru import logger

from bot import NyahBot
from helpers import SuccessEmbed


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot

    @commands.slash_command(
        default_member_permissions=disnake.Permissions(administrator=True)
    )
    async def admin(self, inter: disnake.ApplicationCommandInteraction):
        """Top-level command group for admin commands."""
        pass

    @admin.sub_command()
    async def setup(
        self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel
    ):
        """Bind the channel for Waifu Wars in this server.

        Parameters
        ----------
        channel: :class:`disnake.TextChannel`
            The channel to bind.
        """
        nyah_guild = await self.bot.mongo.fetch_nyah_guild(inter.guild)
        nyah_guild.waifu_war_channel_id = channel.id
        await self.bot.mongo.update_nyah_guild(nyah_guild)
        logger.info(
            f"{inter.author.name}[{inter.author.id}] binded {channel.name}[{channel.id}] for Waifu Wars in {inter.guild.name}[{inter.guild.id}]."
        )
        return await inter.response.send_message(
            embed=SuccessEmbed(f"Succesfully bound {channel.mention}!")
        )

    @admin.sub_command()
    async def settings(self, inter: disnake.ApplicationCommandInteraction):
        """View the server config and binded channels."""
        nyah_guild = await self.bot.mongo.fetch_nyah_guild(inter.guild)
        channel = self.bot.get_channel(nyah_guild.waifu_war_channel_id)
        embed = disnake.Embed(
            title=f"{inter.guild.name} Config",
            description=f"**Bound Channel:** {channel.mention} [{channel.id}]\n",
            color=disnake.Color.blue(),
        ).set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        if inter.guild.icon:
            embed.set_thumbnail(url=inter.guild.icon.url)
        return await inter.response.send_message(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))

import codecs
import datetime

import disnake
from disnake.ext import commands

from bot import NyahBot
from helpers import SuccessEmbed, ErrorEmbed
from utils import Cooldowns
import utils.utilities as utils

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
        """ Top-level command group for owner commands. """
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

    @owner.sub_command()
    async def create_waifu_war(
        self,
        inter: disnake.ApplicationCommandInteraction,
        time_delta_min: int
    ):
        """ Create a Waifu War event manually.
        
            Parameters
            ----------
            time_delta_min: `int`
                How many minutes in the future to schedule for.
        """
        await inter.response.defer(ephemeral=True)
        waifu_war_event = await self.bot.waifus_cog.get_waifu_war_event(inter.guild)
        if waifu_war_event:
            return await inter.edit_original_response(
                embed=ErrorEmbed("A waifu war event already exists!")
            )
        start_time = disnake.utils.utcnow() + datetime.timedelta(minutes=time_delta_min)
        await self.bot.waifus_cog.schedule_waifu_war_event(inter.guild, start_time)
        return await inter.edit_original_response(
            embed=SuccessEmbed(f"Scheduled event for {utils.get_dyn_date_long_time_long(start_time)}")
        )

    @owner.sub_command()
    async def set_user_attributes(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User,
        level: int = None,
        xp: int = None,
        mmr: int = None,
        money: int = None
    ):
        """ Set attributes for a user.
        
            Parameters
            ----------
            user: `disnake.User`
                The user to set attributes for.
        """
        if level == None and xp == None and mmr == None and money == None:
            return await inter.response.send_message(
                embed=ErrorEmbed("No attributes provided!"),
                ephemeral=True
            )
        
        nyah_player = await self.bot.mongo.fetch_nyah_player(user)
        if level != None: nyah_player.level = level
        if xp != None: nyah_player.xp = xp
        if mmr != None: nyah_player.score = mmr
        if money != None: nyah_player.money = money
        await self.bot.mongo.update_nyah_player(nyah_player)

        return await inter.response.send_message(
            embed=SuccessEmbed("Updated user attributes!"),
            ephemeral=True
        )

    @owner.sub_command()
    async def reset_user_cooldown(
        self,
        inter: disnake.ApplicationCommandInteraction,
        cooldown: Cooldowns,
        user: disnake.User = None,
    ):
        """ Resets a chosen cooldown for a user or for all guild members.

            Parameters
            ----------
            cooldown: `Cooldowns`
                The cooldown to reset.
            user: `disnake.User`
                The user to reset waifu availability for. (Default: All guild members)
        """
        cooldown = Cooldowns(cooldown)
        if user:
            nyah_player = await self.bot.mongo.fetch_nyah_player(user)
            await nyah_player.reset_cooldown(cooldown)
            self.bot.logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                                    f"Reset `{cooldown}` for {user.name}#{user.discriminator}[{user.id}]!")
            return await inter.response.send_message(
                embed=SuccessEmbed(f"Reset `{cooldown}` for {user.name}#{user.discriminator}[{user.id}]!"),
                ephemeral=True
            )
        else:
            await self.bot.mongo.update_all_nyah_players(f"timestamp_last_{cooldown.name.lower()}", None)
            self.bot.logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                                    f"Reset `{cooldown}` for all members!")
            return await inter.response.send_message(
                embed=SuccessEmbed(f"Reset `{cooldown}` for all members!"),
                ephemeral=True
            )

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(Owner(bot))
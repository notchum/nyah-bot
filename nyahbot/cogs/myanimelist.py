import os

import disnake
from disnake.ext import commands

from bot import NyahBot
from nyahbot.util import utilities

nsfw_map = {
    "white": "SFW",
    "gray": "Maybe NSFW",
    "black": "NSFW"
}

class MyAnimeList(commands.Cog):
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

    @commands.slash_command()
    async def anime(
        self,
        inter: disnake.ApplicationCommandInteraction,
        anime_name: str
    ):
        """ Get info on an anime series.

            Parameters
            ----------
            anime_name: `str`
                Name of the anime to retrieve.
        """
        await inter.response.defer()
        headers = {"X-MAL-CLIENT-ID": self.bot.config.MAL_CLIENT_ID}
        params  = {"fields" : "id,title,main_picture,start_date,end_date,synopsis,mean,genres,status,num_episodes,media_type,rating,nsfw"}
        try:
            async with self.bot.session.get(url=f"https://api.myanimelist.net/v2/anime?q={anime_name}", headers=headers) as response:
                if response.status != 200:
                    return await inter.edit_original_response(embed=utilities.get_error_embed(f"MAL API returned status code `{response.status}`"))
                body = await response.json()
            async with self.bot.session.get(url=f"https://api.myanimelist.net/v2/anime/{body['data'][0]['node']['id']}", params=params, headers=headers) as response:
                if response.status != 200:
                    return await inter.edit_original_response(embed=utilities.get_error_embed(f"MAL API returned status code `{response.status}`"))
                ani_details = await response.json()
        except Exception as err:
            return await inter.edit_original_response(
                embed=utilities.get_error_embed(f"MAL API returned invalid data! It might be broken right now - try again later.\n```\n{err}```")
            )
        embed = disnake.Embed(
            title=f"{ani_details['title']} [{ani_details['rating'].upper() if 'rating' in ani_details else 'N/A'}] [{nsfw_map[ani_details['nsfw']]}]",
            description=ani_details['synopsis'],
            color=disnake.Color.magenta()
        )
        embed.add_field(
            name="Info",
            value=(f"Score:`{ani_details['mean'] if 'mean' in ani_details else 'N/A'}/10` | Type:`{ani_details['media_type']}`\n"
                   f"Episodes:`{ani_details['num_episodes']}` | Status:`{ani_details['status'].replace('_', ' ').title()}`")
        )
        if 'end_date' in ani_details:
            ani_dates = f"Start:`{ani_details['start_date']}`\n \
                          End:`{ani_details['end_date']}`"
        else:
            ani_dates = f"Start:`{ani_details['start_date']}`"
        embed.add_field(
            name="Dates",
            value=ani_dates,
            inline=True
        )
        ani_genres = '`\n`'.join([genre['name'] for genre in ani_details['genres']])
        embed.add_field(
            name="Genres",
            value=f"`{ani_genres}`",
            inline=True
        )
        embed.add_field(
            name="Links",
            value=f"[MyAnimeList](https://myanimelist.net/anime/{ani_details['id']})",
            inline=False
        )
        embed.set_thumbnail(url=ani_details['main_picture']['medium'])
        return await inter.edit_original_response(embed=embed)

    @commands.slash_command()
    async def manga(
        self,
        inter: disnake.ApplicationCommandInteraction,
        manga_name: str
    ):
        """ Get info on an manga series.

            Parameters
            ----------
            manga_name: `str`
                Name of the manga to retrieve.
        """
        await inter.response.defer()
        headers = {"X-MAL-CLIENT-ID": self.bot.config.MAL_CLIENT_ID}
        params  = {"fields" : "id,title,main_picture,start_date,end_date,synopsis,mean,genres,status,num_chapters,num_volumes,media_type,nsfw"}
        try:
            async with self.bot.session.get(url=f"https://api.myanimelist.net/v2/manga?q={manga_name}", headers=headers) as response:
                if response.status != 200:
                    return await inter.edit_original_response(embed=utilities.get_error_embed(f"MAL API returned status code `{response.status}`"))
                body = await response.json()
            async with self.bot.session.get(url=f"https://api.myanimelist.net/v2/manga/{body['data'][0]['node']['id']}", params=params, headers=headers) as response:
                if response.status != 200:
                    return await inter.edit_original_response(embed=utilities.get_error_embed(f"MAL API returned status code `{response.status}`"))
                mga_details = await response.json()
        except Exception as err:
            return await inter.edit_original_response(
                embed=utilities.get_error_embed(f"MAL API returned invalid data! It might be broken right now - try again later.\n```\n{err}```")
            )
        embed = disnake.Embed(
            title=f"{mga_details['title']} [{nsfw_map[mga_details['nsfw']]}]",
            description=mga_details['synopsis'],
            color=disnake.Color.magenta()
        )
        embed.add_field(
            name="Info",
            value=(f"Status:`{mga_details['status'].replace('_', ' ').title()}` | Score:`{mga_details['mean'] if 'mean' in mga_details else 'N/A'}/10`\n"
                   f"Chapters:`{mga_details['num_chapters']}` | Volumes:`{mga_details['num_volumes']}`\n"
                   f"Type:`{mga_details['media_type'].title()}`")
        )
        if 'end_date' in mga_details:
            mga_dates = f"Start:`{mga_details['start_date']}`\n \
                          End:`{mga_details['end_date']}`"
        else:
            mga_dates = f"Start:`{mga_details['start_date']}`"
        embed.add_field(
            name="Dates",
            value=mga_dates,
            inline=True
        )
        mga_genres = '`\n`'.join([genre['name'] for genre in mga_details['genres']])
        embed.add_field(
            name="Genres",
            value=f"`{mga_genres}`",
            inline=True
        )
        embed.add_field(
            name="Links",
            value=f"[MyAnimeList](https://myanimelist.net/manga/{mga_details['id']})",
            inline=False
        )
        embed.set_thumbnail(url=mga_details['main_picture']['medium'])
        return await inter.edit_original_response(embed=embed)

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(MyAnimeList(bot))
import os
import re

import disnake
from   disnake.ext import commands, tasks

from lxml import html
from loguru import logger
from rethinkdb import r

from nyahbot.util import utilities
from nyahbot.util.globals import conn, session
from nyahbot.util.dataclasses import (
    Waifu,
)

class Scraper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.waifu_scraper.start()
        #!!! REMOVE
        self.scraper_index = 10000
        self.last_check_unranked = False
        #!!! REMOVE

    ##*************************************************##
    ##********           ABSTRACTIONS           *******##
    ##*************************************************##

    ##*************************************************##
    ##********              EVENTS              *******##
    ##*************************************************##

    ##*************************************************##
    ##********              TASKS               *******##
    ##*************************************************##

    @tasks.loop(seconds=15.0)
    async def waifu_scraper(self):
        """ Scrapes waifu info from the site. """
        logger.debug(f"Scraping waifu... [loop #{self.waifu_scraper.current_loop}]")
        
        unranked_str = "This waifu has not been ranked site-wide yet"
        days_suffix = ["st", "nd", "rd", "th"]
        months = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12
        }

        h = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0",
            "Accept-Language": "en-US,en;q=0.5"
        }

        #!!! REMOVE
        waifu_core_count = r.db("waifus").table("core").count().run(conn)
        if self.last_check_unranked:
            self.scraper_index += 1
            self.last_check_unranked = False
        if self.scraper_index > waifu_core_count - 1:
            self.waifu_scraper.stop()
        else:
            entry_needs_updated = False
            while not entry_needs_updated:
                result = r.db("waifus").table("core").nth(self.scraper_index).run(conn)
                entry = Waifu(**result)
                if not entry.popularity_rank:
                    entry_needs_updated = True
                else:
                    self.scraper_index += 1

        try:
            response = await session.get(url=f"{os.environ['WEBSCRAPE_URL']}{entry.slug}", headers=h, proxy=os.environ["PROXY_HTTP_URL"])
        except Exception as e:
            self.scraper_index += 1 #!!! REMOVE
            return logger.error(e)
        #!!! REMOVE

        # try:
        #     response = await session.get(url=os.environ["WEBSCRAPE_URL"], headers=h, proxy=os.environ["PROXY_HTTP_URL"])
        # except Exception as e:
        #     return logger.error(e)

        try:
            if response.status != 200:
                self.scraper_index += 1 #!!! REMOVE
                return logger.error(f"{response.url} returned status {response.status}!")

            # get slug
            slug = response.real_url.name
            if len(slug) > 127:
                self.scraper_index += 1 #!!! REMOVE
                return logger.error(f"RethinkDB cannot insert primary key '{slug}' due to too many characters")
            logger.info(f"Retrieved webpage for '{slug}'")

            # parse html
            body = await response.text()
            elem = html.fromstring(body)

            # scrape
            core_info = elem.cssselect("#waifu-core-information")[0]
            new_waifu = Waifu(
                url=f"{os.environ['WEBSCRAPE_URL']}{slug}",
                source="mywaifulist",
                name=elem.cssselect("h1.my-3")[0].text,
                original_name=core_info.cssselect("#alternate-name")[0].text,
                romaji_name=core_info.cssselect("#romaji-name")[0].text,
                description=core_info.cssselect("#description")[0].text,
                image_url=elem.cssselect("img.h-full")[0].attrib["src"],
                series=[i.text for i in core_info.cssselect("div.md\:text-left:nth-child(2) a")],
                origin=core_info.cssselect("#origin")[0].text,
                husbando=True if elem.cssselect("#waifu-classification") else False,
                height=core_info.cssselect("#height")[0].text,
                weight=core_info.cssselect("#weight")[0].text,
                blood_type=core_info.cssselect("#blood-type")[0].text,
                bust=core_info.cssselect("#bust")[0].text,
                waist=core_info.cssselect("#waist")[0].text,
                hip=core_info.cssselect("#hip")[0].text,
                age=core_info.cssselect("#age")[0].text,
                date_of_birth=core_info.cssselect("#birthday")[0].text,
                birthday_day=None,
                birthday_month=None,
                birthday_year=None,
                popularity_rank=core_info.cssselect("#popularity-rank")[0].text_content() if unranked_str not in body else None,
                like_rank=core_info.cssselect("#like-rank")[0].text_content() if unranked_str not in body else None,
                trash_rank=core_info.cssselect("#trash-rank")[0].text_content() if unranked_str not in body else None,
                slug=slug,
                tags=[i.text for i in elem.cssselect("div.mt-2:nth-child(4) span")],
            )

            # pipeline
            new_waifu.name = new_waifu.name.strip()
            new_waifu.tags = [tag.strip().lower() for tag in new_waifu.tags if tag != "Remove Tag"]
            if unranked_str not in body:
                new_waifu.popularity_rank = int(re.findall("\d+", new_waifu.popularity_rank)[0])
                new_waifu.like_rank = int(re.findall("\d+", new_waifu.like_rank)[0])
                new_waifu.trash_rank = int(re.findall("\d+", new_waifu.trash_rank)[0])
            else:
                self.last_check_unranked = True
            if new_waifu.date_of_birth:
                for value in new_waifu.date_of_birth.split(" "):
                    # if the string matches one of the months, then it is a month
                    if value in months.keys():
                        new_waifu.birthday_month = months[value]

                    # if the string has a suffix from days_suffix and a number, then it is a day
                    elif any(bool(re.search(r"\d", value)) and suf in value for suf in days_suffix):
                        new_waifu.birthday_day = int(re.search(r"\d+", value).group())
                    
                    # if the string is only numbers, then assume it is a year
                    elif value.isdigit():
                        new_waifu.birthday_year = int(value)
            
            # if it exists in db, then update it
            exists = r.db("waifus") \
                        .table("core") \
                        .get_all(slug) \
                        .count() \
                        .eq(1) \
                        .run(conn)
            if exists:
                logger.info(f"'{slug}' already exists in the database; checking for updates...")
                result = r.db("waifus") \
                            .table("core") \
                            .get(slug) \
                            .run(conn)
                db_waifu = Waifu(**result)
                if new_waifu == db_waifu:
                    logger.info(f"'{slug}' is up-to-date in the database; moving on...")
                    return
                logger.info(f"'{slug}' is not up-to-date in the database; attempting to update...")

                differences = Waifu.compare(db_waifu, new_waifu)
                for field, value in differences.items():
                    old = value["old"]
                    new = value["new"]
                    logger.info(f"    ├─'{field}' ({old} -> {new})")

                result = r.db("waifus") \
                            .table("core") \
                            .get(slug) \
                            .update(new_waifu.__dict__) \
                            .run(conn)
                if result["replaced"]:
                    logger.success(f"Updated database entry for '{slug}'")
                else:
                    logger.error(f"Failed to replace database entry for '{slug}'")

            # insert the new waifu in the db
            else:
                logger.warning(f"'{slug}' doesn't exist in the database; attempting to create an entry...")
                result = r.db("waifus") \
                            .table("core") \
                            .insert(new_waifu.__dict__) \
                            .run(conn)
                if result["inserted"]:
                    logger.success(f"Created database entry for '{slug}'")
                else:
                    logger.error(f"Failed to create database entry for '{slug}'")
        
        except Exception as e:
            logger.exception(e)

            # await self.bot.owner.send(
            #     embed=disnake.Embed(
            #         title=slug,
            #         url=f"{os.environ["WEBSCRAPE_URL"]}{slug}",
            #         color=disnake.Color.random(),
            #         description=f"{utilities.get_dyn_time_long(disnake.utils.utcnow())}"
            #                     f"{utilities.create_trace(e)}",
            #     ),
            # )
        
        self.scraper_index += 1 #!!! REMOVE

    @waifu_scraper.before_loop
    async def init_waifu_scraper(self):
        await self.bot.wait_until_ready()

    ##*************************************************##
    ##********             COMMANDS             *******##
    ##*************************************************##

    @commands.slash_command(default_member_permissions=disnake.Permissions(administrator=True))
    async def scraper(self, inter: disnake.ApplicationCommandInteraction):
        """ Top-level command group for scraper operations. """
        pass

    @scraper.sub_command()
    async def kickstart(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @scraper.sub_command()
    async def halt(self, inter: disnake.ApplicationCommandInteraction):
        pass

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    required_env_vars = ["PROXY_HTTP_URL", "WEBSCRAPE_URL"]
    for env_var in required_env_vars:
        if env_var not in os.environ or not os.environ[env_var]:
            return logger.error(f"Cannot load cog 'Scraper' | {env_var} not in environment!")
    bot.add_cog(Scraper(bot))
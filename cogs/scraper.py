import re

import disnake
from disnake.ext import commands, tasks
from lxml import html

from bot import NyahBot
from models import Waifu

class Scraper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot
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
        self.bot.logger.debug(f"Scraping waifu... [loop #{self.waifu_scraper.current_loop}]")
        
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
        waifu_core_count = await self.bot.mongo.fetch_waifu_count()
        if self.last_check_unranked:
            self.scraper_index += 1
            self.last_check_unranked = False
        if self.scraper_index > waifu_core_count - 1:
            self.waifu_scraper.stop()
        else:
            entry_needs_updated = False
            while not entry_needs_updated:
                entry = await self.bot.mongo.fetch_waifu_by_index(self.scraper_index)
                if not entry.popularity_rank:
                    entry_needs_updated = True
                else:
                    self.scraper_index += 1

        try:
            response = await self.bot.session.get(
                url=f"{self.bot.config.WEBSCRAPE_URL}{entry.slug}",
                headers=h,
                proxy=self.bot.config.PROXY_HTTP_URL
            )
        except Exception as e:
            self.scraper_index += 1 #!!! REMOVE
            return self.bot.logger.error(e)
        #!!! REMOVE

        # try:
        #     response = await self.bot.session.get(
        #         url=self.bot.config.WEBSCRAPE_URL,
        #         headers=h,
        #         proxy=self.bot.config.PROXY_HTTP_URL
        #     )
        # except Exception as e:
        #     return self.bot.logger.error(e)

        try:
            if response.status != 200:
                self.scraper_index += 1 #!!! REMOVE
                return self.bot.logger.error(f"{response.url} returned status {response.status}!")

            # get slug
            slug = response.real_url.name
            if len(slug) > 127:
                self.scraper_index += 1 #!!! REMOVE
                return self.bot.logger.error(f"RethinkDB cannot insert primary key '{slug}' due to too many characters")
            self.bot.logger.info(f"Retrieved webpage for '{slug}'")

            # parse html
            body = await response.text()
            elem = html.fromstring(body)

            # scrape
            core_info = elem.cssselect("#waifu-core-information")[0]
            new_waifu = Waifu(
                url=f"{self.bot.config.WEBSCRAPE_URL}{slug}",
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
                new_waifu.popularity_rank = int(re.findall(r'\d+', new_waifu.popularity_rank)[0])
                new_waifu.like_rank = int(re.findall(r'\d+', new_waifu.like_rank)[0])
                new_waifu.trash_rank = int(re.findall(r'\d+', new_waifu.trash_rank)[0])
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
            exists = await self.bot.mongo.check_waifu_exists(slug)
            if exists:
                self.bot.logger.info(f"'{slug}' already exists in the database; checking for updates...")
                db_waifu = await self.bot.mongo.fetch_waifu(slug)
                if new_waifu == db_waifu:
                    self.bot.logger.info(f"'{slug}' is up-to-date in the database; moving on...")
                    return
                self.bot.logger.info(f"'{slug}' is not up-to-date in the database; attempting to update...")

                differences = Waifu.compare(db_waifu, new_waifu)
                for field, value in differences.items():
                    old = value["old"]
                    new = value["new"]
                    self.bot.logger.info(f"    ├─'{field}' ({old} -> {new})")

                await self.bot.mongo.update_waifu(new_waifu)
                self.bot.logger.info(f"Updated database entry for '{slug}'")

            # insert the new waifu in the db
            else:
                self.bot.logger.warning(f"'{slug}' doesn't exist in the database; attempting to create an entry...")
                await self.bot.mongo.insert_waifu(new_waifu)
                self.bot.logger.info(f"Created database entry for '{slug}'")
        
        except Exception as e:
            self.bot.logger.exception(e)

            # await self.bot.owner.send(
            #     embed=disnake.Embed(
            #         title=slug,
            #         url=f"{self.bot.config.WEBSCRAPE_URL}{slug}",
            #         color=disnake.Color.random(),
            #         description=f"{disnake.utils.format_dt(disnake.utils.utcnow(), "D")}"
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
    bot.add_cog(Scraper(bot))
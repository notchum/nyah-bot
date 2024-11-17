import os
import shutil
import tempfile
import platform
from collections import namedtuple
from typing import Dict

import aiohttp_client_cache
import disnake
from disnake import Activity, ActivityType
from disnake.ext import commands
from loguru import logger
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image

import models
import utils
from helpers import Mongo, API

VERSION = "0.9.0"

Config = namedtuple(
    "Config",
    [
        "DEBUG",
        "DISNAKE_LOGGING",
        "TEST_MODE",
        "DISCORD_BOT_TOKEN",
        "DATABASE_URI",
        "MAL_CLIENT_ID",
    ],
)


class NyahBot(commands.InteractionBot):
    def __init__(self, *args, **kwargs):
        self.config: Config = kwargs.pop("config", None)
        self.version = VERSION
        super().__init__(*args, **kwargs)
        self.before_slash_command_invoke(self.before_invoke)
        self.after_slash_command_invoke(self.after_invoke)
        self.activity = Activity(type=ActivityType.watching, name=f"v{VERSION}")
    
    async def setup_hook(self):
        # Initialize temporary directory
        self.create_temp_dir()
        logger.debug(f"Initialized temp directory {self.temp_dir}")

        # Load cogs
        for extension in utils.get_cog_names():
            try:
                self.load_extension(extension)
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                logger.exception(
                    f"Failed to load extension {extension}!\t{exception}"
                )

        # Initialize database
        self.client = AsyncIOMotorClient(self.config.DATABASE_URI, io_loop=self.loop)
        if self.config.TEST_MODE:
            await init_beanie(self.client["waifus"], document_models=[models.Waifu])
            await init_beanie(self.client["_nyah"], document_models=[models.NyahConfig, models.NyahGuild, models.NyahPlayer])
            await init_beanie(self.client["_waifus"], document_models=[models.Claim])
            await init_beanie(self.client["_wars"], document_models=[models.Event, models.Match, models.Battle, models.Round, models.Vote])
            logger.warning("Running in test mode. Connected to test database.")
        else:
            await init_beanie(self.client["nyah"], document_models=[models.NyahConfig, models.NyahGuild, models.NyahPlayer])
            await init_beanie(self.client["waifus"], document_models=[models.Waifu, models.Claim])
            await init_beanie(self.client["wars"], document_models=[models.Event, models.Match, models.Battle, models.Round, models.Vote])
            logger.success("Connected to database.")

        # Create the global bot settings entry if it doesn't exist
        await self.create_settings_entry()
        
        # Initialize aiohttp session
        self.session = aiohttp_client_cache.CachedSession(
            cache=aiohttp_client_cache.CacheBackend(expire_after=600),
            loop=self.loop
        )

        # Set up interfaces
        self.api = API(self.session, self.temp_dir)
        self.mongo = Mongo()

    async def on_ready(self):
        # fmt: off
        logger.info("------")
        logger.info(f"{self.user.name} v{self.version}")
        logger.info(f"ID: {self.user.id}")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Disnake API version: {disnake.__version__}")
        logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        logger.info("------")
        # fmt: on

    async def close(self):
        await self.session.close()
        await super().close()

    def create_temp_dir(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), "tmp-nyah-bot")
        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)

    def clear_temp_dir(self):
        for file in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Error deleting {file}: {e}")

    async def create_settings_entry(self):
        return #TODO remove when settings is renamed
        settings_doc = await models.BotSettings.find_all().to_list()
        if len(settings_doc) == 0:
            settings_doc = await models.BotSettings.insert_one(
                models.BotSettings(toggle=False)
            )
            logger.success(f"Created settings entry for nyah-bot [{settings_doc.id}]")

    @property
    def waifus_cog(self) -> commands.Cog:
        return self.get_cog("Waifus")

    async def before_invoke(self, inter: disnake.ApplicationCommandInteraction):
        nyah_player = await models.NyahPlayer.find_one(
            models.NyahPlayer.user_id == inter.author.id
        )
        
        channel_id = nyah_player.last_command_channel_id
        message_id = nyah_player.last_command_message_id
        if not channel_id or not message_id:
            return
        
        # grab the channel
        # p_channel = self.get_partial_messageable(channel_id, type=disnake.TextChannel)
        channel = self.get_channel(channel_id)
        if not channel:
            channel = await self.fetch_channel(channel_id)
        
        # attempt to grab the message partial
        p_message = channel.get_partial_message(message_id)
        if p_message:
            return await p_message.edit(view=None)
        
        # if that fails, fetch the message
        message = await channel.fetch_message(message_id)
        if message:
            return await message.edit(view=None)

    async def after_invoke(self, inter: disnake.ApplicationCommandInteraction):
        nyah_player = await models.NyahPlayer.find_one(
            models.NyahPlayer.user_id == inter.author.id
        )
        
        message = await inter.original_response()
        if not message.components or message.flags.ephemeral:
            nyah_player.last_command_name = None
            nyah_player.last_command_channel_id = None
            nyah_player.last_command_message_id = None
        else:
            nyah_player.last_command_name = inter.data.name
            nyah_player.last_command_channel_id = inter.channel.id
            nyah_player.last_command_message_id = message.id
        
        await nyah_player.save()

    async def upload_image_to_discord(self, path_file: os.PathLike | str | disnake.File) -> disnake.Attachment:
        """Upload the image to discord (free image hosting)"""
        image_host_channel = await self.fetch_channel(1164613880538992760)
        if isinstance(path_file, (os.PathLike, str)):
            image_host_msg = await image_host_channel.send(file=disnake.File(path_file))
        elif isinstance(path_file, disnake.File):
            image_host_msg = await image_host_channel.send(file=path_file)
        else:
            raise TypeError(f"{path_file} must be of type os.PathLike or disnake.File")
        logger.info(f"Uploaded image {image_host_msg.attachments[0].url}")
        return image_host_msg.attachments[0]

    async def create_waifu_vs_img(self, red_waifu: models.Claim, blue_waifu: models.Claim) -> str:
        """ Create a waifu war round versus thumbnail image.
            Red is on the left and blue is on the right.

            Get ready to see the worst code ever written.

            Parameters
            ----------
            red_waifu: `Claim`
                The waifu to place on the red side of the versus image.
            blue_waifu: `Claim`
                The waifu to place on the blue side of the versus image.

            Returns
            -------
            `str`
                The URL of the versus image.
        """
        UPPER_LEFT_INX = 0
        LOWER_RIGHT_INX = 1
        X_COORD_INX = 0
        Y_COORD_INX = 1

        def scale_image(img: Image.Image, scale_percent: float) -> Image.Image:
            """ Scales an image to `scale_percent`. """
            dim = (int(img.width * scale_percent), int(img.height * scale_percent))
            return img.resize(dim, resample=Image.Resampling.BICUBIC)

        def get_bounding_box_coords(img: Image.Image) -> list:
            """ Returns the coordinates of two boxes.  """
            return [
                # (x0, y0), (x1, y1)
                [(int(img.width*0.10), int(img.height*0.10)), (int(img.width*0.40), int(img.height*0.90))], # left side
                # (x2, y2), (x3, y3)
                [(int(img.width*0.60), int(img.height*0.10)), (int(img.width*0.90), int(img.height*0.90))]  # right side
            ]

        def center_place(img: Image.Image, bb_coords: list) -> tuple:
            """ Calculate upper-left coordinate to place an image in center of bounding box. """
            bb_width = bb_coords[LOWER_RIGHT_INX][X_COORD_INX] - bb_coords[UPPER_LEFT_INX][X_COORD_INX]
            bb_height = bb_coords[LOWER_RIGHT_INX][Y_COORD_INX] - bb_coords[UPPER_LEFT_INX][Y_COORD_INX]
            center_x = bb_coords[UPPER_LEFT_INX][X_COORD_INX] + bb_width//2
            center_y = bb_coords[UPPER_LEFT_INX][Y_COORD_INX] + bb_height//2

            return (center_x - img.width//2, center_y - img.height//2)

        # create the output path
        output_path = os.path.join(self.temp_dir, f"{red_waifu.id}.vs.{blue_waifu.id}.png")

        # check if the image already exists
        if os.path.exists(output_path):
            attachment = await self.upload_image_to_discord(output_path)
            return attachment.url

        # load background
        bg_img = Image.open("assets/vs.jpg") # "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fstatic.vecteezy.com%2Fsystem%2Fresources%2Fpreviews%2F000%2F544%2F945%2Foriginal%2Fcomic-fighting-cartoon-background-blue-vs-red-vector-illustration-design.jpg&f=1&nofb=1&ipt=d7b1d0d9bb512e200148263e80ad893ee95f011cf44cfc20417a2da90f94642a&ipo=images"
        if (bg_img.mode != "RGBA"):
            bg_img = bg_img.convert("RGBA")

        # get initial bounding box coords [upper-left, lower-right]
        bb = get_bounding_box_coords(bg_img)

        # load 2 foreground images
        waifus: Dict[str, Dict[str, Image.Image | models.Claim | int]] = {
            "red": {
                "object": red_waifu,
                "image": None,
                "long_inx": None
            },
            "blue": {
                "object": blue_waifu,
                "image": None,
                "long_inx": None
            },
        }
        for waifu_color, waifu_value in waifus.items():
            # get claim
            claim = waifu_value["object"]

            # download image
            image_path = await self.api.download_image(claim.image_url)

            # load fg image
            load_img = Image.open(image_path)
            if (load_img.mode != "RGBA"):
                load_img = load_img.convert("RGBA")
            
            # save the image
            waifus[waifu_color]["image"] = load_img

            # determine longer side of each fg image
            if waifus[waifu_color]["image"].height > waifus[waifu_color]["image"].width:
                waifus[waifu_color]["long_inx"] = 1 # 1=height in .size
            else:
                waifus[waifu_color]["long_inx"] = 0 # 0=width in .size
        
        # determine the smaller image of the two using total pixels
        if (waifus["red"]["image"].width * waifus["red"]["image"].height) < (waifus["blue"]["image"].width * waifus["blue"]["image"].height):
            small_img_key = "red"
            large_img_key = "blue"
        else:
            small_img_key = "blue"
            large_img_key = "red"
        
        # get length of bb side-of-interest
        bb_long = bb[0][LOWER_RIGHT_INX][waifus[small_img_key]["long_inx"]] - bb[0][UPPER_LEFT_INX][waifus[small_img_key]["long_inx"]]
        if waifus[small_img_key]["image"].size[waifus[small_img_key]["long_inx"]] < bb_long: # if the smaller fg is smaller than the bb
            # scale the bg image
            scale_percent = waifus[small_img_key]["image"].size[waifus[small_img_key]["long_inx"]] / bb_long
            bg_img = scale_image(bg_img, scale_percent)

            # scale the bb to the new bg size
            bb = get_bounding_box_coords(bg_img)

            # scale the larger fg to the new bb size
            bb_long = bb[0][LOWER_RIGHT_INX][waifus[large_img_key]["long_inx"]] - bb[0][UPPER_LEFT_INX][waifus[large_img_key]["long_inx"]]
            scale_percent = bb_long / waifus[large_img_key]["image"].size[waifus[large_img_key]["long_inx"]]
            waifus[large_img_key]["image"] = scale_image(waifus[large_img_key]["image"], scale_percent)
        else: # if the bb is smaller than the smaller fg
            # scale both fg images to the bb
            for key, waifu_value in waifus.items():
                fg_img = waifu_value["image"]
                long_inx = waifu_value["long_inx"]
                bb_long = bb[0][LOWER_RIGHT_INX][long_inx] - bb[0][UPPER_LEFT_INX][long_inx]
                scale_percent = bb_long / fg_img.size[long_inx]
                waifus[key]["image"] = scale_image(fg_img, scale_percent)

        # final scaling and overlaying
        for bb_inx, (_, waifu_value) in enumerate(waifus.items()):
            fg_img = waifu_value["image"]
            # in case a fg image's width is too wide for the bb, scale once more
            bb_width = bb[bb_inx][LOWER_RIGHT_INX][X_COORD_INX] - bb[bb_inx][UPPER_LEFT_INX][X_COORD_INX]
            if fg_img.width > bb_width:
                scale_percent = bb_width / fg_img.width
                fg_img = scale_image(fg_img, scale_percent)

            # overlay fg images onto bg
            bg_img.paste(fg_img, box=center_place(fg_img, bb[bb_inx]), mask=fg_img)

        # save the image
        bg_img.save(output_path)
        logger.info(f"Created image {output_path}")

        # upload the image
        attachment = await self.upload_image_to_discord(output_path)

        # return the URL of the image
        return attachment.url

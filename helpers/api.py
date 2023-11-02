import os
import logging

import aiofiles
import aiohttp_client_cache

logger = logging.getLogger("nyahbot")

class API():
    def __init__(self, session: aiohttp_client_cache.CachedSession, cache_dir: str) -> None:
        self.session = session
        self.cache_dir = cache_dir

    async def download_image(self, url: str) -> str | None:
        """ Download an image from a URL.

            LIMIT: N/A
        
            Returns
            -------
            `str`: The path to the downloaded image.
        """
        try:
            image_filename = os.path.basename(url)
            image_path = os.path.join(self.cache_dir, image_filename)

            if not os.path.exists(image_path):
                async with self.bot.session.get(url) as response:
                    if response.status != 200:
                        self.bot.logger.error(f"Downloading image {url} returned status code `{response.status}`")
                        return None
                    async with aiofiles.open(image_path, mode="wb") as f:
                        await f.write(await response.read())
                    self.bot.logger.info(f"Downloaded image {image_path}")
            return image_path
        except Exception as err:
            self.bot.logger.error(f"Downloading image returned invalid data! {err}")
            return None

    async def search_jikan_series(self, query: str) -> str | None:
        """ Search for an anime series on MyAnimeList using Jikan.

            LIMIT: Limited to 3 requests per second.
        
            Returns
            -------
            `str`: The URL of the series found. `None` if no series was found.
        """
        request_url = f"https://api.jikan.moe/v4/anime?q={query}"
        try:
            async with self.session.get(url=request_url, timeout=3) as response:
                if response.status != 200:
                    return None
                body = await response.json()
                if body["pagination"]["items"]["total"] > 0:
                    return body["data"][0]["url"] # grab the first series returned
                else:
                    return None
        except Exception as e:
            logger.error(f"Jikan API failed! GET='{request_url}' REASON={e}")
            return None

    async def search_mal_series(self, query: str) -> str | None:
        """ Search for an anime series on MyAnimeList.

            LIMIT: N/A
        
            Returns
            -------
            `str`: The URL of the series found. `None` if no series was found.
        """
        if "MAL_CLIENT_ID" not in os.environ or not os.environ["MAL_CLIENT_ID"]:
            return None
        
        request_url = f"https://api.myanimelist.net/v2/anime?q={query}"
        headers = {"X-MAL-CLIENT-ID": os.environ["MAL_CLIENT_ID"]}
        try:
            async with self.session.get(url=request_url, headers=headers, timeout=3) as response:
                if response.status != 200:
                    return None
                body = await response.json()
                if not body:
                    return None
                else:
                    return f"https://myanimelist.net/anime/{body['data'][0]['node']['id']}" # grab the first series returned
        except Exception as e:
            logger.error(f"MAL API failed! GET='{request_url}' REASON={e}")
            return None
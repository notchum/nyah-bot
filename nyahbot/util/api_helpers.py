import os

from loguru import logger

from nyahbot.util.globals import session

async def search_jikan_series(query: str) -> str | None:
    """ Search for an anime series on MyAnimeList using Jikan.

        LIMIT: Limited to 3 requests per second.
    
        Returns
        -------
        `str`
            The URL of the series found.
            `None` if no series was found.
    """
    request_url = f"https://api.jikan.moe/v4/anime?q={query}"
    try:
        async with session.get(url=request_url, timeout=3) as response:
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

async def search_mal_series(query: str) -> str | None:
    """ Search for an anime series on MyAnimeList.

        LIMIT: N/A
    
        Returns
        -------
        `str`
            The URL of the series found.
            `None` if no series was found.
    """
    if "MAL_CLIENT_ID" not in os.environ or not os.environ["MAL_CLIENT_ID"]:
        return None
    
    request_url = f"https://api.myanimelist.net/v2/anime?q={query}"
    headers = {"X-MAL-CLIENT-ID": os.environ["MAL_CLIENT_ID"]}
    try:
        async with session.get(url=request_url, headers=headers, timeout=3) as response:
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
import re
import datetime
import traceback

import disnake

##*************************************************##
##********          DISCORD UTILS           *******##
##*************************************************##

def get_success_embed(description: str) -> disnake.Embed:
    """ Creates a simple embed for successful Discord bot commands.

        Parameters
        ----------
        description: `str`
            The description to add to the embed; usually the
            error message of what was successful.

        Returns
        -------
        `disnake.Embed`: The embed created.          
    """
    return disnake.Embed(
        title="Success! ✅",
        description=description,
        color=disnake.Color.green()
    )

def get_error_embed(description: str) -> disnake.Embed:
    """ Creates a simple embed for Discord bot command errors.

        Parameters
        ----------
        description: `str`
            The description to add to the embed; usually the
            error message of what went wrong.

        Returns
        -------
        `disnake.Embed`: The embed created.          
    """
    return disnake.Embed(
        title="Error! 💢",
        description=description,
        color=disnake.Color.red()
    )

def get_dyn_time_relative(t: datetime.datetime) -> str:
    """ Get a dynamic date-time display in your Discord messages. 
    
        Parameters
        ----------
        t: `datetime:datetime`
            The time to get a timestamp for.
    """
    return f"<t:{int(t.timestamp())}:R>"

def get_dyn_time_long(t: datetime.datetime) -> str:
    """ Get a dynamic date-time display in your Discord messages. 
    
        Parameters
        ----------
        t: `datetime:datetime`
            The time to get a timestamp for.
    """
    return f"<t:{int(t.timestamp())}:F>"

def get_dyn_time_short(t: datetime.datetime) -> str:
    """ Get a dynamic date-time display in your Discord messages. 
    
        Parameters
        ----------
        t: `datetime:datetime`
            The time to get a timestamp for.
    """
    return f"<t:{int(t.timestamp())}:t>"

##*************************************************##
##********          GENERAL UTILS           *******##
##*************************************************##

def create_trace(err: Exception, advance: bool = True) -> str:
    """ A way to debug your code anywhere.

        Parameters
        ----------
        err: `Exception`
            The exception to trace
        advance: `bool`
            +++. (Default: True)

        Returns
        -------
        `str`: A formatted string of the debug trace
    """
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = ('```py\n{1}{0}: {2}\n```').format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"

def chunkify(to_chunk: str) -> list:
    """ Split up a long string into 1000 character substrings.

        Parameters
        ----------
        to_chunk: `str`
            The string to split up
        
        Returns
        -------
        `list`: A list containing the 'chunks' of strings capped
            at 1000 characters each
    """
    len_chunks = -(len(to_chunk) // -1000) # upside-down floor (ceiling)
    chunks = []
    for i in range(len_chunks):
        chunked_str = to_chunk[(1000 * i) : (1000 if i == 0 else 1000 * (i + 1))]
        chunks.append(chunked_str)
    return chunks

def extract_uuid(input_string: str) -> str | None:
    """ Extract the UUID from any string.

        Parameters
        ----------
        input_string: `str`
            A string that has a UUID.
        
        Returns
        -------
        `str`: The UUID or `None` if no UUID is found.
    """
    # Regular expression to match any version 4 UUID
    uuid_pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"
    
    # Find the first matching UUID in the input string
    uuid_match = re.search(uuid_pattern, input_string)
    
    if uuid_match:
        return uuid_match.group()
    else:
        return None

import logging
import logging.config
import asyncio
from typing import Union, Optional, AsyncGenerator

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrofork").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

try:
    from pyrofork import Client, __version__
    from pyrofork.raw.all import layer
    from pyrofork import types
except ImportError:
    print("Pyrofork not found! Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "pyrofork==2.3.68"])
    from pyrofork import Client, __version__
    from pyrofork.raw.all import layer
    from pyrofork import types

from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, PORT
from utils import temp
from Script import script
from datetime import date, datetime
import pytz

class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=200,  # Increased for better performance
            plugins={"root": "plugins"},
            sleep_threshold=10,
            max_concurrent_transmissions=4  # Better resource management
        )

    async def start(self):
        """Start the bot with enhanced initialization"""
        try:
            # Get banned users and chats
            b_users, b_chats = await db.get_banned()
            temp.BANNED_USERS = b_users
            temp.BANNED_CHATS = b_chats
            
            await super().start()
            await Media.ensure_indexes()
            
            me = await self.get_me()
            temp.ME = me.id
            temp.U_NAME = me.username
            temp.B_NAME = me.first_name
            self.username = '@' + me.username if me.username else 'Unknown'
            
            logging.info(f"{me.first_name} started with Pyrofork v{__version__} (Layer {layer}) on {me.username}")
            logging.info(LOG_STR)
            logging.info(script.LOGO)
            
            # Send startup message with timezone
            tz = pytz.timezone('Asia/Kolkata')
            today = date.today()
            now = datetime.now(tz)
            time = now.strftime("%H:%M:%S %p")
            
            if LOG_CHANNEL:
                try:
                    await self.send_message(
                        chat_id=LOG_CHANNEL, 
                        text=script.RESTART_TXT.format(today, time)
                    )
                except Exception as e:
                    logging.error(f"Failed to send startup message: {e}")
                    
        except Exception as e:
            logging.error(f"Bot startup failed: {e}")
            raise

    async def stop(self, *args):
        """Graceful shutdown"""
        try:
            await super().stop()
            logging.info("Bot stopped gracefully.")
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """
        Iterate through a chat sequentially with improved error handling.
        
        This convenience method does the same as repeatedly calling :meth:`~pyrofork.Client.get_messages` 
        in a loop, thus saving you from the hassle of setting up boilerplate code. 
        It is useful for getting the whole chat messages with a single call.

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            limit (``int``):
                Identifier of the last message to be returned.

            offset (``int``, *optional*):
                Identifier of the first message to be returned.
                Defaults to 0.

        Returns:
            ``Generator``: A generator yielding :obj:`~pyrofork.types.Message` objects.

        Example:
            .. code-block:: python

                async for message in app.iter_messages("pyrofork", 1, 15000):
                    print(message.text)
        """
        current = offset
        
        while True:
            try:
                new_diff = min(200, limit - current)
                if new_diff <= 0:
                    return

                messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
                
                for message in messages:
                    if message:  # Check if message exists
                        yield message

                current += 1
                
                # Add small delay to prevent rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Error in iter_messages: {e}")
                break

# Initialize and run bot
if __name__ == "__main__":
    try:
        app = Bot()
        app.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")


app = Bot()
app.run()

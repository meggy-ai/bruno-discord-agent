# bruno/integrations/discord_text_bot.py
import os, logging, asyncio
from datetime import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv
from bruno_core.models import Message as BrunoMessage
from app.lib.common import get_agent
import app.crud.user as user_crud
from app.db.session import get_db_session
from app.db.models import Conversation, Message
from app.lib.memory_store import MemoryStore
from app.lib.user_manager import UserManager


# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bruno.discord.text")

class DiscordTextBot:
    def __init__(self, token: str, cooldown_seconds: int = 2):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.token = token
        self.user_last_message = {}  # user_id -> datetime
        self.cooldown_seconds = cooldown_seconds
        self.bruno_agent = get_agent()
        self.db = get_db_session()
        self.memory_store = MemoryStore(self.db)
        self.user_manager = UserManager(self.db)
        
        self._register_handlers()

    def _check_rate_limit(self, user_id: int) -> bool:
        now = datetime.now()
        last = self.user_last_message.get(user_id)
        if last and (now - last).total_seconds() < self.cooldown_seconds:
            return False
        self.user_last_message[user_id] = now
        return True

    def _split_and_send(self, channel, text: str, max_len: int = 2000):
        async def send_chunks():
            if len(text) <= max_len:
                await channel.send(text)
                return
            paragraphs = text.split('\n\n')
            chunk = ""
            for p in paragraphs:
                if len(chunk) + len(p) + 2 <= max_len:
                    chunk += p + "\n\n"
                else:
                    if chunk:
                        await channel.send(chunk.strip())
                    chunk = p + "\n\n"
            if chunk:
                await channel.send(chunk.strip())
        return send_chunks()

    def _register_handlers(self):
        @self.bot.event
        async def on_ready():
            logger.info(f"Logged in as {self.bot.user} (id={self.bot.user.id})")

        @self.bot.event
        async def on_message(message: discord.Message):
            # check if the message is from a bot
            if message.author.bot:
                return
            # respond to DMs or messages containing "bruno" (configurable)
            is_dm = isinstance(message.channel, discord.DMChannel)
            if not is_dm and "bruno" not in message.content.lower() and self.bot.user not in message.mentions:
                return
            # rate limit to check if user is sending messages too quickly
            if not self._check_rate_limit(message.author.id):
                return
            
            response = await self._handle_text_message(message, str(message.author.id), message.author.name)  
            response_text = response.text if response else "Sorry, I couldn't process your request."
            await self._split_and_send(message.channel, response_text)

    async def _handle_text_message(self, message: discord.Message, user_id: str, username: str) -> str:
        print(f"Processing command from {username} ({user_id}): {message.content}")

        content = message.content.strip()
            # Remove trigger word
        content_clean = content.lower().replace("bruno", "", 1).strip() or content
        if not content_clean:
            content_clean = content  # Keep original if nothing left
        

        # Show typing indicator
        show_typing = True

        async with message.channel.typing() if show_typing else asyncio.nullcontext():
            user = self.user_manager.get_user_by_username(username)
            
            conversation = self.memory_store.get_conversations_for_user(user.id)
            if not conversation:
                conversation = self.memory_store.create_conversation(user.id, title="Discord Conversation")
            
            
            self.memory_store.add_message(
                conversation_id=conversation.id,
                role="user",
                content=content
            )
            msg = BrunoMessage(
                    role="user",
                    content=content
                )
            response = await self.bruno_agent.process_message(msg)
            self.memory_store.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response.text
            )
            return response

    def run(self):
        self.bot.run(self.token)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Set DISCORD_TOKEN")
    bot = DiscordTextBot(token=token)
    bot.run()
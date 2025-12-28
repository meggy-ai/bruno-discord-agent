# bruno/integrations/discord_text_bot.py
import os, logging, asyncio
from datetime import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv

from app.core.abilities.notes_ability import NotesAbility
from app.core.abilities.timer_ability import TimerAbility
from app.core.bruno_agent import AgentConfig, BrunoAgent
from app.core.bruno_llm import OllamaClient
from app.core.bruno_memory import MemoryManager
from bruno_core.models import Message as BrunoMessage

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bruno.discord.text")

class SimpleDiscordTextBot:
    def __init__(self, token: str, cooldown_seconds: int = 2):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.token = token
        self.user_last_message = {}  # user_id -> datetime
        self.cooldown_seconds = cooldown_seconds
        config = AgentConfig(
                name="sample_agent",
                model="mistral:7b"
            )
        # Create LLM client
        llm_client = OllamaClient(
            base_url="http://localhost:11434",
            model="mistral:7b"
        )
        notes_ability = NotesAbility()
        timer_ability = TimerAbility()
        memory_manager = MemoryManager()
        # Create Bruno agent
        self.bruno_agent = BrunoAgent(
            config=config,
            llm_client=llm_client,
            memory_manager=memory_manager,
            notes_ability=notes_ability,
            timer_ability=timer_ability
        )
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
            if message.author.bot:
                return
            # respond to DMs or messages containing "bruno" (configurable)
            is_dm = isinstance(message.channel, discord.DMChannel)
            if not is_dm and "bruno" not in message.content.lower() and self.bot.user not in message.mentions:
                return
            if not self._check_rate_limit(message.author.id):
                return
            content = message.content.strip()
            # Remove trigger word
            content_clean = content.lower().replace("bruno", "", 1).strip() or content
            # Call your command processor (replace this with actual LLM call)
            msg = BrunoMessage(
                role="user",
                content=content_clean
            )
            response = await self.bruno_agent.process_message(msg)
            response_text = response.text if response else "Sorry, I couldn't process your request."
            await self._split_and_send(message.channel, response_text)

    async def process_command_stub(self, command: str, user_id: str, username: str) -> str:
        # Replace with call to your LLM or service. Simple echo for now.
        await asyncio.sleep(0)  # keep async
        return f"Echo from bot: {command}"

    def run(self):
        self.bot.run(self.token)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Set DISCORD_TOKEN")
    bot = SimpleDiscordTextBot(token=token)
    bot.run()
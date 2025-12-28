import asyncio
from app.db.session import SessionLocal
from app.crud.user import create_user
from app.core.bruno_agent import BrunoAgent, AgentConfig
from app.core.bruno_llm import OllamaClient
from app.core.bruno_memory import MemoryManager
from app.core.abilities.notes_ability import NotesAbility
from app.core.abilities.timer_ability import TimerAbility
from bruno_core.models import Message, AssistantResponse, ConversationContext
import os


db = SessionLocal()

async def main():
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
    bruno_agent = BrunoAgent(
        config=config,
        llm_client=llm_client,
        memory_manager=memory_manager,
        notes_ability=notes_ability,
        timer_ability=timer_ability
    )

    msg = Message(
        role="user",
        content="Hey, whats the capital of brazil?"
    )
    response = await bruno_agent.process_message(msg)
    print(f"Hello, Bruno Discord Agent! Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
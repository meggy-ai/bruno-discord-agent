
from logging import config
from app.core.abilities.notes_ability import NotesAbility
from app.core.abilities.timer_ability import TimerAbility
from app.core.bruno_agent import AgentConfig, BrunoAgent
from app.core.bruno_llm import OllamaClient
from app.core.bruno_memory import MemoryManager
from bruno_core.interfaces import LLMInterface
import os

def get_agent_config() -> AgentConfig:
    return AgentConfig(
        name="default_agent",
        model=os.getenv("LLM_MODEL"),
        llm_provider=os.getenv("LLM_PROVIDER"),
        base_url=os.getenv("LLM_API_URL")
    )

def get_llm_client() -> LLMInterface:
    config = get_agent_config()
    if config.llm_provider == "ollama":
        return OllamaClient(
            base_url=config.base_url,
            model=config.model
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")

def get_agent() -> BrunoAgent:
    notes_ability = NotesAbility()
    timer_ability = TimerAbility()
    memory_manager = MemoryManager()
    llm_client = get_llm_client()
    agent = BrunoAgent(
        config=get_agent_config(),
        llm_client=llm_client,
        memory_manager=memory_manager,
        notes_ability=notes_ability,
        timer_ability=timer_ability
    )
    return agent    



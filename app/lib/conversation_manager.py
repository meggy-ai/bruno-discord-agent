from app.lib.memory_store import MemoryStore


class ConversationManager:
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
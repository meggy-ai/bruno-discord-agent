from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import uuid

# Import interfaces from published bruno packages
from bruno_core.interfaces import MemoryInterface
from bruno_core.models import Message, MessageRole, MessageType
from bruno_core.models.context import SessionContext, ConversationContext, UserContext
from bruno_core.models.memory import MemoryEntry, MemoryQuery, MemoryType

logger = logging.getLogger(__name__)

class MemoryManager(MemoryInterface):
    """Manages conversation history and context, implementing MemoryInterface."""
    
    def __init__(self, db_backend=None):
        """
        Initialize memory manager.
        
        Args:
            db_backend: Database backend for persistent storage (optional)
        """
        self.db_backend = db_backend
        self.in_memory_cache: Dict[str, List[Dict]] = {}
        self._sessions: Dict[str, SessionContext] = {}
        logger.info("Initialized MemoryManager")
    
    # Implementation of MemoryInterface methods
    async def store_message(
        self,
        message: Message,
        conversation_id: str
    ) -> None:
        """Store a message in memory."""
        message_dict = {
            "role": message.role.value if hasattr(message.role, 'value') else str(message.role),
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata or {}
        }
        
        # Add to in-memory cache
        if conversation_id not in self.in_memory_cache:
            self.in_memory_cache[conversation_id] = []
        self.in_memory_cache[conversation_id].append(message_dict)
        
        # Persist to database if backend is available
        if self.db_backend:
            await self.db_backend.save_message(conversation_id, message_dict)
        
        logger.debug(f"Stored message in conversation {conversation_id}")
    
    async def retrieve_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Retrieve messages from a conversation."""
        # Try to get from database first
        message_dicts = []
        if self.db_backend:
            message_dicts = await self.db_backend.get_messages(conversation_id, limit)
        
        # Fallback to in-memory cache
        if not message_dicts:
            message_dicts = self.in_memory_cache.get(conversation_id, [])
            if limit:
                message_dicts = message_dicts[-limit:]
        
        # Convert dicts to Message objects
        messages = []
        for msg_dict in message_dicts:
            try:
                role_str = msg_dict.get("role", "user")
                role = MessageRole(role_str) if role_str in [r.value for r in MessageRole] else MessageRole.USER
                
                messages.append(Message(
                    role=role,
                    content=msg_dict["content"],
                    message_type=MessageType.TEXT,
                    timestamp=datetime.fromisoformat(msg_dict.get("timestamp", datetime.utcnow().isoformat())),
                    metadata=msg_dict.get("metadata", {}),
                    conversation_id=conversation_id
                ))
            except Exception as e:
                logger.error(f"Error converting message dict to Message: {e}")
                continue
        
        logger.debug(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
        return messages
    
    async def search_messages(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Message]:
        """Search messages by text query."""
        # Simple text search implementation
        results = []
        for conv_id, messages in self.in_memory_cache.items():
            for msg_dict in messages:
                if query.lower() in msg_dict["content"].lower():
                    try:
                        role_str = msg_dict.get("role", "user")
                        role = MessageRole(role_str) if role_str in [r.value for r in MessageRole] else MessageRole.USER
                        
                        results.append(Message(
                            role=role,
                            content=msg_dict["content"],
                            message_type=MessageType.TEXT,
                            timestamp=datetime.fromisoformat(msg_dict.get("timestamp", datetime.utcnow().isoformat())),
                            metadata=msg_dict.get("metadata", {}),
                            conversation_id=conv_id
                        ))
                    except Exception as e:
                        logger.error(f"Error converting message: {e}")
                        continue
                
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
        
        return results[:limit]
    
    async def store_memory(self, memory_entry: MemoryEntry) -> None:
        """Store a memory entry (fact, preference, etc.)."""
        # Simplified implementation - store in cache
        # In a real implementation, this would go to a vector database
        logger.info(f"Storing memory entry: {memory_entry.content[:50]}...")
    
    async def retrieve_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve memories matching query criteria."""
        # Simplified implementation
        logger.info(f"Retrieving memories for user: {query.user_id}")
        return []
    
    async def delete_memory(self, memory_id: str) -> None:
        """Delete a memory entry."""
        logger.info(f"Deleting memory: {memory_id}")
    
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionContext:
        """Create a new conversation session."""
        session = SessionContext(
            user_id=user_id,
            metadata=metadata or {}
        )
        self._sessions[session.session_id] = session
        logger.info(f"Created session {session.session_id} for user {user_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)
    
    async def end_session(self, session_id: str) -> None:
        """End a conversation session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Ended session {session_id}")
    
    async def get_context(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> ConversationContext:
        """Get conversation context for a user."""
        user = UserContext(user_id=user_id)
        session = await self.get_session(session_id) if session_id else await self.create_session(user_id)
        
        context = ConversationContext(
            conversation_id=str(uuid.uuid4()),
            user=user,
            session=session,
            messages=[],
            max_messages=20
        )
        return context
    
    async def clear_history(
        self,
        conversation_id: str,
        keep_system_messages: bool = True
    ) -> None:
        """Clear message history for a conversation."""
        if conversation_id in self.in_memory_cache:
            if keep_system_messages:
                self.in_memory_cache[conversation_id] = [
                    msg for msg in self.in_memory_cache[conversation_id]
                    if msg["role"] == "system"
                ]
            else:
                del self.in_memory_cache[conversation_id]
        
        if self.db_backend:
            await self.db_backend.clear_conversation(conversation_id)
        
        logger.info(f"Cleared history for conversation {conversation_id}")
    
    async def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user."""
        # Simplified implementation
        total_messages = sum(len(msgs) for msgs in self.in_memory_cache.values())
        return {
            "total_messages": total_messages,
            "conversations": len(self.in_memory_cache),
            "memories": 0
        }
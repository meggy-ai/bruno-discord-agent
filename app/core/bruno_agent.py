from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# Import interfaces from published bruno_core package
from bruno_core.interfaces import AssistantInterface
from bruno_core.models import Message, AssistantResponse, ConversationContext
from bruno_core.models.response import ActionResult, ActionStatus

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: str = "You are Bruno, a helpful AI assistant."
    llm_provider: str = "ollama"

class BrunoAgent(AssistantInterface):
    """Core Bruno AI Agent implementing AssistantInterface."""
    def __init__(self, config: AgentConfig, llm_client, memory_manager=None, notes_ability=None, timer_ability=None):
        self.config = config
        self.llm_client = llm_client
        self.memory_manager = memory_manager
        self.notes_ability = notes_ability
        self.timer_ability = timer_ability
        self._abilities: Dict[str, Any] = {}
        self._is_initialized = False
        logger.info(f"Initialized BrunoAgent: {config.name} with {config.llm_provider}/{config.model}")
    # Implementation of AssistantInterface methods
    async def initialize(self) -> None:
        """Initialize the assistant and all its components."""
        if self._is_initialized:
            return
        
        # Initialize abilities if provided
        if self.timer_ability:
            self._abilities['timer'] = self.timer_ability
        if self.notes_ability:
            self._abilities['notes'] = self.notes_ability
            
        self._is_initialized = True
        logger.info(f"Assistant {self.config.name} initialized")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the assistant and cleanup resources."""
        self._is_initialized = False
        self._abilities.clear()
        logger.info(f"Assistant {self.config.name} shutdown")
    
    async def register_ability(self, ability: Any) -> None:
        """Register a new ability with the assistant."""
        ability_name = getattr(ability, 'name', ability.__class__.__name__)
        self._abilities[ability_name] = ability
        logger.info(f"Registered ability: {ability_name}")
    
    async def unregister_ability(self, ability_name: str) -> None:
        """Unregister an ability from the assistant."""
        if ability_name in self._abilities:
            del self._abilities[ability_name]
            logger.info(f"Unregistered ability: {ability_name}")
    
    async def get_abilities(self) -> List[str]:
        """Get list of registered ability names."""
        return list(self._abilities.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health status of assistant and its components."""
        health = {
            "status": "healthy" if self._is_initialized else "not_initialized",
            "llm": "connected",  # TODO: Check actual LLM connection
            "memory": "ready" if self.memory_manager else "not_configured",
            "abilities": list(self._abilities.keys())
        }
        return health
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get assistant metadata."""
        return {
            "name": self.config.name,
            "model": self.config.model,
            "provider": self.config.llm_provider,
            "version": "1.0.0"
        }
    
    async def process_message(
        self,
        message: Message,
        context: Optional[ConversationContext] = None
    ) -> AssistantResponse:
        """
        Process a user message and generate a response.
        
        Args:
            message: User message to process
            context: Optional conversation context (created if None)
            
        Returns:
            Assistant response with text and actions
        """
        try:
            if not self._is_initialized:
                await self.initialize()
            
            user_message = message.content
            conversation_id = message.conversation_id or "default"
            user_id = context.user.user_id if context and context.user else None
            metadata = message.metadata or {}
            # Check if this is a timer command first
            if self.timer_ability and user_id:
                timer_response = self.timer_ability.handle_timer_command(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    command=user_message
                )
                if timer_response:
                    # This was a timer command - return timer response
                    action_result = ActionResult(   
                        action_type="timer",
                        status=ActionStatus.SUCCESS,
                        message=timer_response
                    )
                    return AssistantResponse(
                        text=timer_response,
                        actions=[action_result],
                        success=True,
                        metadata={"is_timer_response": True}
                    )
            
            # Check if this is a notes command
            if self.notes_ability and user_id:
                notes_response =  self.notes_ability.handle_notes_command(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    command=user_message
                )
                if notes_response:
                    # This was a notes command - return notes response
                    action_result = ActionResult(
                        action_type="notes",
                        status=ActionStatus.SUCCESS,
                        message=notes_response
                    )
                    return AssistantResponse(
                        text=notes_response,
                        actions=[action_result],
                        success=True,
                        metadata={"is_notes_response": True}
                    )
            

            # Get conversation history from memory if available
            conversation_history = []
            # if self.memory_manager:
            #     conversation_history = self.memory_manager.get_history(
            #         conversation_id, limit=10
            #     )
            
            logger.info(f"Conversation history retrieved: {len(conversation_history)} messages for {conversation_id}")
            for i, msg in enumerate(conversation_history):
                logger.info(f"  History {i+1}: [{msg['role']}] {msg['content'][:50]}...")
            
            # Build messages for LLM
            system_prompt = self.config.system_prompt
            
            # For task commands, prepend instruction for concise response
            is_task_command = metadata.get("is_task_command", False)
            if is_task_command:
                logger.info("🔍 Task command detected - using concise response mode")
                system_prompt = (
                    "**CRITICAL INSTRUCTION: This is a TASK COMMAND (timer/reminder/note). "
                    "You MUST respond with EXACTLY ONE SHORT sentence confirming the task. "
                    "Example: 'Timer set for 4 minutes.' or '4-minute timer started.' "
                    "DO NOT add any conversational text, questions, or additional commentary. "
                    "JUST confirm the task action in 5-10 words maximum.**\n\n"
                    + system_prompt
                )
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Inject long-term memories into context if available (skip for task commands)
            # if user_id and not is_task_command:
            #     from core.bruno_integration.memory_extraction import memory_extractor
            #     memory_context = await memory_extractor.format_memories_for_context(user_id, limit=10)
            #     if memory_context:
            #         messages.append({
            #             "role": "system",
            #             "content": memory_context
            #         })
            #         logger.info(f"Injected long-term memories into context for user {user_id}")
            
            # Add conversation history (excluding the last user message if it matches current input)
            # This prevents duplicate messages when the current user message is already in history
            for msg in conversation_history:
                # Skip if this is the current user message (already in DB before this function is called)
                if msg["role"] == "user" and msg["content"] == user_message:
                    continue
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message (might be duplicate from history, but we ensure uniqueness above)
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            logger.info(f"Total messages being sent to LLM: {len(messages)}")
            
            # Generate response using LLM
            response = await self.llm_client.generate(
                messages=messages,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # Note: Messages are saved to database by views.py, not here
            # Memory manager only reads from database for conversation history
            
            return AssistantResponse(
                text=response,
                actions=[],
                success=True,
                metadata={
                    "model": self.config.model,
                    "tokens_used": self.get_token_count(response) if hasattr(self, 'get_token_count') else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return AssistantResponse(
                text="I apologize, but I encountered an error processing your message. Please try again.",
                actions=[],
                success=False,
                error=str(e),
                metadata={
                    "model": self.config.model,
                    "tokens_used": 0
                }
            )
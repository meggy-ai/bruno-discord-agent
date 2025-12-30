from typing import Dict, Any, Optional
import logging
# Import interfaces from published bruno packages
from bruno_abilities import BaseAbility, AbilityMetadata, ParameterMetadata
from bruno_abilities.base.ability_base import AbilityContext, AbilityResult

logger = logging.getLogger(__name__)

class NotesState:
    """Tracks the state of the notes interface for each conversation."""
    def __init__(self):
        self.conversation_states: Dict[str, Dict[str, Any]] = {}
    
    def get_state(self, conversation_id: str) -> Dict[str, Any]:
        """Get state for a conversation."""
        if conversation_id not in self.conversation_states:
            self.conversation_states[conversation_id] = {
                'in_notes_mode': False,
                'current_note_id': None,
                'view': 'none'  # 'none', 'list', 'detail'
            }
        return self.conversation_states[conversation_id]
    
    def set_state(self, conversation_id: str, **kwargs):
        """Update state for a conversation."""
        state = self.get_state(conversation_id)
        state.update(kwargs)
    
    def exit_notes(self, conversation_id: str):
        """Exit notes mode."""
        self.conversation_states[conversation_id] = {
            'in_notes_mode': False,
            'current_note_id': None,
            'view': 'none'
        }


# Global notes state manager
notes_state = NotesState()

class NotesAbility(BaseAbility):
    """Manages note-taking functionality for Bruno, extending BaseAbility."""
    
    def __init__(self):
        super().__init__()
        from app.db.models import Note, NoteEntry
        self.Note = Note
        self.NoteEntry = NoteEntry
        logger.info("Initialized NotesAbility")
    
    @property
    def metadata(self) -> AbilityMetadata:
        """Return metadata describing this ability."""
        return AbilityMetadata(
            name="notes",
            description="Manage notes and journal entries",
            version="1.0.0",
            parameters=[
                ParameterMetadata(
                    name="command",
                    type=str,
                    description="Notes command to execute",
                    required=True
                ),
                ParameterMetadata(
                    name="conversation_id",
                    type=str,
                    description="Conversation ID for state tracking",
                    required=False
                )
            ]
        )
    
    def _execute(self, parameters: dict[str, Any], context: AbilityContext) -> AbilityResult:
        """Internal execution method implementing the ability logic."""
        command = parameters.get("command", "")
        user_id = context.user_id
        conversation_id = parameters.get("conversation_id", "default")
        
        # Handle notes command using legacy method
        response = self.handle_notes_command(user_id, conversation_id, command)
        
        if response:
            return AbilityResult(
                success=True,
                message=response
            )
        else:
            return AbilityResult(
                success=False,
                message="Not a notes command"
            )
    
    def handle_notes_command(
        self,
        user_id: str,
        conversation_id: str,
        command: str
    ) -> str:
        print("Handling notes command is called, needs to be implemented")
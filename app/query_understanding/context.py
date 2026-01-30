"""Context augmentation using session memory and recent messages."""

from typing import List, Dict, Any, Optional
from app.memory.schemas import SessionMemory


class ContextAugmenter:
    """Augments query context with session memory and recent messages."""
    
    def augment(
        self,
        query: str,
        recent_messages: List[Dict[str, Any]],
        session_memory: Optional[SessionMemory] = None,
        needed_fields: List[str] = None
    ) -> tuple[str, List[str]]:
        """
        Augment query context with relevant memory and messages.
        
        Args:
            query: User query
            recent_messages: Recent conversation messages
            session_memory: Session memory summary (optional)
            needed_fields: List of memory fields needed (e.g., ['user_profile.prefs', 'open_questions'])
            
        Returns:
            Tuple of (augmented_context_text, fields_used)
        """
        fields_used = []
        context_parts = []
        
        # Add recent messages context
        if recent_messages:
            recent_context = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in recent_messages[-5:]  # Last 5 messages
            ])
            context_parts.append(f"Recent conversation:\n{recent_context}")
        
        # Add relevant memory fields
        if session_memory and needed_fields:
            memory_parts = []
            summary = session_memory.session_summary
            
            for field in needed_fields:
                if field == "user_profile.prefs" and summary.user_profile.prefs:
                    memory_parts.append(f"User preferences: {', '.join(summary.user_profile.prefs)}")
                    fields_used.append(field)
                elif field == "user_profile.constraints" and summary.user_profile.constraints:
                    memory_parts.append(f"User constraints: {', '.join(summary.user_profile.constraints)}")
                    fields_used.append(field)
                elif field == "key_facts" and summary.key_facts:
                    memory_parts.append(f"Key facts: {', '.join(summary.key_facts)}")
                    fields_used.append(field)
                elif field == "decisions" and summary.decisions:
                    memory_parts.append(f"Decisions: {', '.join(summary.decisions)}")
                    fields_used.append(field)
                elif field == "open_questions" and summary.open_questions:
                    memory_parts.append(f"Open questions: {', '.join(summary.open_questions)}")
                    fields_used.append(field)
                elif field == "todos" and summary.todos:
                    memory_parts.append(f"Todos: {', '.join(summary.todos)}")
                    fields_used.append(field)
            
            if memory_parts:
                context_parts.append(f"Relevant session memory:\n" + "\n".join(f"- {part}" for part in memory_parts))
        
        # If no specific fields requested, intelligently select relevant ones
        elif session_memory:
            summary = session_memory.session_summary
            # Simple keyword matching to determine relevance
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['prefer', 'like', 'want', 'need']):
                if summary.user_profile.prefs:
                    context_parts.append(f"User preferences: {', '.join(summary.user_profile.prefs)}")
                    fields_used.append("user_profile.prefs")
            
            if any(word in query_lower for word in ['question', 'ask', 'wonder']):
                if summary.open_questions:
                    context_parts.append(f"Open questions: {', '.join(summary.open_questions)}")
                    fields_used.append("open_questions")
            
            if any(word in query_lower for word in ['todo', 'task', 'action', 'do']):
                if summary.todos:
                    context_parts.append(f"Todos: {', '.join(summary.todos)}")
                    fields_used.append("todos")
        
        augmented_context = "\n\n".join(context_parts) if context_parts else ""
        return augmented_context, fields_used

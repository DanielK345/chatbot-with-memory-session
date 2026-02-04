"""
Context augmentation using session memory and recent messages.

Per fix.txt section 4 (CONTEXT RETRIEVAL):
- Default: last 1 user + assistant turn
- Expand to max 3 turns ONLY if: unresolved pronoun, contrast words, conflicting signals
- Session summary: Include ONLY key_facts, decisions, user_profile.prefs
- Do NOT include: todos, open_questions (unless directly referenced)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.memory.schemas import SessionMemory, SessionSummary, UserProfile, MessageRange


class ContextAugmenter:
    """
    Augments query context with selective session memory retrieval.
    
    Principle: Limit context size aggressively per fix.txt.
    """
    
    def augment(
        self,
        query: str,
        recent_messages: List[Dict[str, Any]],
        session_memory: Optional[SessionMemory] = None,
        needed_fields: List[str] = None,
        max_context_turns: int = 1
    ) -> tuple[str, List[str]]:
        """
        Augment query context with selective memory and message retrieval.
        
        Args:
            query: User query
            recent_messages: Recent conversation messages
            session_memory: Session memory summary (optional)
            needed_fields: List of memory fields to include (defaults to key fields per fix.txt)
            max_context_turns: Max conversation turns to include (default 1, can expand to 3)
            
        Returns:
            Tuple of (augmented_context_text, fields_used_from_memory)
        """
        fields_used = []
        context_parts = []
        
        # STEP 1: Determine which memory fields to include (aggressive selection)
        if needed_fields is None:
            # Default: only these per fix.txt section 4
            needed_fields = ["user_profile.prefs", "key_facts", "decisions"]
        
        # STEP 2: Add recent messages context (minimal by default)
        if recent_messages:
            num_turns = min(max_context_turns, len(recent_messages) // 2)
            if num_turns == 0:
                num_turns = 1
            
            # Get last N turns (each turn = user + assistant)
            messages_to_include = recent_messages[-(num_turns * 2):]
            
            if messages_to_include:
                recent_context = "\n".join([
                    f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')}"
                    for msg in messages_to_include
                ])
                context_parts.append(f"Recent conversation:\n{recent_context}")
        
        # STEP 3: Add selective session memory fields (aggressive filtering per fix.txt)
        if session_memory:
            memory_parts = []
            summary = session_memory.session_summary
            
            for field in needed_fields:
                # Only include fields that actually have content
                if field == "user_profile.prefs" and summary.user_profile.prefs:
                    prefs_str = ", ".join(summary.user_profile.prefs)
                    memory_parts.append(f"User preferences: {prefs_str}")
                    fields_used.append(field)
                    
                elif field == "user_profile.constraints" and summary.user_profile.constraints:
                    constraints_str = ", ".join(summary.user_profile.constraints)
                    memory_parts.append(f"User constraints: {constraints_str}")
                    fields_used.append(field)
                    
                elif field == "key_facts" and summary.key_facts:
                    facts_str = "; ".join(summary.key_facts)
                    memory_parts.append(f"Key facts: {facts_str}")
                    fields_used.append(field)
                    
                elif field == "decisions" and summary.decisions:
                    decisions_str = "; ".join(summary.decisions)
                    memory_parts.append(f"Decisions: {decisions_str}")
                    fields_used.append(field)
                    
                elif field == "open_questions" and summary.open_questions:
                    # Only include if explicitly requested (not by default per fix.txt)
                    open_q_str = "; ".join(summary.open_questions)
                    memory_parts.append(f"Open questions: {open_q_str}")
                    fields_used.append(field)
            
            # Only add memory section if we found relevant fields
            if memory_parts:
                context_parts.append("Relevant session memory:\n- " + "\n- ".join(memory_parts))
        
        # STEP 4: Build final context
        augmented_context = "\n\n".join(context_parts) if context_parts else "(No relevant context)"
        
        return augmented_context, fields_used
    
    def should_expand_context(
        self,
        query: str,
        recent_messages: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Determine if we should expand from 1 turn to 3 turns of context.
        
        Expand context if:
        - Unresolved pronoun (it, they, this, that, he, she)
        - Contrast words (but, however, instead, rather, although)
        - Query seems to reference multiple things
        
        Returns:
            True if should expand context to 3 turns
        """
        query_lower = query.lower()
        
        # Check for pronouns
        pronouns = ['it ', ' it', 'they', 'this ', 'that ', 'he ', 'she ', ' he', ' she']
        has_pronoun = any(pronoun in query_lower for pronoun in pronouns)
        
        # Check for contrast words
        contrast_words = [' but ', ' however', ' instead', ' rather', ' although']
        has_contrast = any(word in query_lower for word in contrast_words)
        
        # Check for multiple references
        if recent_messages:
            recent_text = " ".join([m.get('content', '') for m in recent_messages[-4:]])
            recent_entities = len(set(w for w in recent_text.split() if w[0].isupper()))
            has_multiple_entities = recent_entities > 2
        else:
            has_multiple_entities = False
        
        return has_pronoun or has_contrast or has_multiple_entities
    
if __name__ == "__main__":
    augmenter = ContextAugmenter()
    sample_query = "Why is it faster than the other model?"
    sample_messages = [
        {"role": "user", "content": "Tell me about Llama 3.1."},
        {"role": "assistant", "content": "Llama 3.1 is a state-of-the-art language model."},
        {"role": "user", "content": "How does it compare to Qwen?"},
        {"role": "assistant", "content": "Llama 3.1 is generally faster and more efficient."}
    ]
    sample_memory = SessionMemory(
        session_summary=SessionSummary(
            user_profile=UserProfile(
                prefs=['fast responses', 'concise answers'],
                constraints=[]
            ),
            key_facts=['User prefers fast models', 'Interested in Llama and Qwen'],
            decisions=['Choose Llama for speed'],
            open_questions=[]
        ),
        message_range_summarized=MessageRange(from_index=0, to_index=2)
    )
    
    should_expand = augmenter.should_expand_context(sample_query, sample_messages)
    max_turns = 3 if should_expand else 1
    augmented_context, fields_used = augmenter.augment(
        sample_query,
        sample_messages,
        sample_memory,
        max_context_turns=max_turns
    )
    
    print("Augmented Context:\n", augmented_context)
    print("Fields Used from Memory:", fields_used)


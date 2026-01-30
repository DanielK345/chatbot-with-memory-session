"""Main pipeline orchestrator for chat assistant."""

from typing import List, Dict, Any, Optional, Union
from app.memory.session_store import SessionStore
from app.memory.summarizer import SessionSummarizer
from app.memory.schemas import MessageRange
from app.core.token_counter import TokenCounter
from app.query_understanding.ambiguity import AmbiguityDetector
from app.query_understanding.rewrite import QueryRewriter
from app.query_understanding.context import ContextAugmenter
from app.query_understanding.clarifier import ClarifyingQuestionGenerator
from app.query_understanding.schemas import QueryUnderstanding
from app.core.prompt_builder import PromptBuilder
from app.llm.client import LLMClient
from app.llm.ollama_client import OllamaClient
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ChatPipeline:
    """Main pipeline for processing chat messages."""
    
    def __init__(
        self,
        session_store: SessionStore,
        llm_client: Union[LLMClient, OllamaClient],
        max_context_tokens: int = 10000,
        keep_recent_messages: int = 5
    ):
        """
        Initialize chat pipeline.
        
        Args:
            session_store: Session store instance
            llm_client: LLM client instance (LLMClient or OllamaClient)
            max_context_tokens: Maximum tokens before triggering summarization
            keep_recent_messages: Number of recent messages to keep after summarization
        """
        self.session_store = session_store
        self.llm_client = llm_client
        self.max_context_tokens = max_context_tokens
        self.keep_recent_messages = keep_recent_messages
        
        # Initialize components
        self.token_counter = TokenCounter()
        self.summarizer = SessionSummarizer(llm_client)
        self.ambiguity_detector = AmbiguityDetector(llm_client)
        self.query_rewriter = QueryRewriter(llm_client)
        self.context_augmenter = ContextAugmenter()
        self.clarifier = ClarifyingQuestionGenerator(llm_client)
        self.prompt_builder = PromptBuilder()
    
    async def process_message(
        self,
        session_id: str,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Process a user message through the full pipeline.
        
        Args:
            session_id: Session identifier
            user_query: User's message
            
        Returns:
            Dict with response and pipeline metadata
        """
        logger.info(f"[Pipeline] Processing message for session {session_id}")
        
        # Step 1: Add user message to session
        self.session_store.add_message(session_id, "user", user_query)
        messages = self.session_store.get_messages(session_id)
        
        # Step 2: Check context size and summarize if needed
        token_count = self.token_counter.count_messages(messages)
        logger.info(f"[Pipeline] Token count: {token_count}")
        
        session_memory = None
        if token_count > self.max_context_tokens:
            logger.info(f"[Pipeline] Context exceeded threshold ({token_count} > {self.max_context_tokens}), triggering summarization")
            
            # Determine range to summarize (all except recent messages)
            summarize_to = len(messages) - self.keep_recent_messages
            if summarize_to > 0:
                message_range = MessageRange(from_index=0, to_index=summarize_to)
                session_memory = await self.summarizer.summarize(messages, message_range)
                self.session_store.save_summary(session_id, session_memory)
                
                # Clear old messages, keep recent ones
                self.session_store.clear_messages(session_id, keep_recent=self.keep_recent_messages)
                messages = self.session_store.get_messages(session_id)
                logger.info(f"[Pipeline] Summarized messages 0-{summarize_to}, kept {self.keep_recent_messages} recent messages")
        
        # Get existing summary if available
        if not session_memory:
            session_memory = self.session_store.get_summary(session_id)
        
        # Step 3: Query Understanding Pipeline
        logger.info("[Pipeline] Starting query understanding")
        
        # 3a. Ambiguity detection
        ambiguity_analysis = await self.ambiguity_detector.detect(user_query, messages)
        logger.info(f"[Pipeline] Ambiguity detected: {ambiguity_analysis.is_ambiguous}")
        
        # 3b. Query rewrite (if ambiguous)
        rewritten_query = None
        if ambiguity_analysis.is_ambiguous:
            rewritten_query = await self.query_rewriter.rewrite(
                user_query,
                messages,
                ambiguity_analysis.ambiguity_reason
            )
            logger.info(f"[Pipeline] Query rewritten: {rewritten_query}")
        
        # 3c. Context augmentation
        query_to_use = rewritten_query or user_query
        augmented_context, fields_used = self.context_augmenter.augment(
            query_to_use,
            messages,
            session_memory
        )
        logger.info(f"[Pipeline] Memory fields used: {fields_used}")
        
        # 3d. Generate clarifying questions (if still unclear)
        clarifying_questions = []
        if ambiguity_analysis.is_ambiguous and rewritten_query:
            # Check if rewrite helped - if still ambiguous, generate questions
            # For simplicity, we'll generate questions if original was ambiguous
            clarifying_questions = await self.clarifier.generate(
                user_query,
                rewritten_query,
                messages
            )
            if clarifying_questions:
                logger.info(f"[Pipeline] Generated {len(clarifying_questions)} clarifying questions")
        
        # Build query understanding output
        query_understanding = QueryUnderstanding(
            original_query=user_query,
            is_ambiguous=ambiguity_analysis.is_ambiguous,
            rewritten_query=rewritten_query,
            ambiguity_reason=ambiguity_analysis.ambiguity_reason,
            needed_context_from_memory=fields_used,
            clarifying_questions=clarifying_questions,
            final_augmented_context=augmented_context
        )
        
        # Step 4: Build final prompt
        system_prompt, user_prompt = self.prompt_builder.build(
            query_to_use,
            augmented_context
        )
        
        # Step 5: Generate LLM response
        logger.info("[Pipeline] Generating LLM response")
        llm_response = await self.llm_client.generate(
            prompt=user_prompt,
            system=system_prompt
        )
        
        # Step 6: Add assistant response to session
        self.session_store.add_message(session_id, "assistant", llm_response)
        
        # Return response with metadata
        return {
            "response": llm_response,
            "query_understanding": query_understanding.model_dump(),
            "session_memory": session_memory.model_dump() if session_memory else None,
            "pipeline_metadata": {
                "token_count": token_count,
                "summarization_triggered": token_count > self.max_context_tokens,
                "fields_used_from_memory": fields_used
            }
        }

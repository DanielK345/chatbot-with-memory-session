"""
Main pipeline orchestrator for chat assistant per fix.txt principles.

PIPELINE FLOW:
1. SPELLING CHECK (rule-based, NO LLM)
2. AMBIGUITY CHECK (rule-first, LLM fallback)
3. ANSWERABILITY CHECK (similarity-based, NO LLM)
4. CONTEXT RETRIEVAL (selective, aggressive filtering)
5. QUERY REFINEMENT (rule-based entity replacement)
6. LLM (ONLY if answerable)

DESIGN PRINCIPLES:
- Prefer early exits
- Never guess silently
- Limit context size aggressively
- LLM is last resort, not default
- Target: LLM usage in < 30% of queries
"""

from typing import List, Dict, Any, Optional, Union
from app.memory.session_store import SessionStore
from app.memory.summarizer import SessionSummarizer
from app.memory.schemas import MessageRange
from app.core.token_counter import TokenCounter
from app.query_understanding.spelling_check import SpellingChecker
from app.query_understanding.ambiguity import AmbiguityDetector
from app.query_understanding.answerability_check import AnswerabilityChecker
from app.query_understanding.context import ContextAugmenter
from app.query_understanding.query_refiner import QueryRefiner
from app.query_understanding.clarifier import ClarifyingQuestionGenerator
from app.query_understanding.schemas import QueryUnderstanding, AmbiguityAnalysis, AnswerabilityAnalysis
from app.core.prompt_builder import PromptBuilder
from app.llm.client import LLMClient
from app.llm.ollama_client import OllamaClient
from app.llm.gemini_client import GeminiClient
from app.utils.logging import get_logger, ConversationLogger, UserQueryLogger, SessionSummaryLogger

logger = get_logger(__name__)


class ChatPipeline:
    """
    Main pipeline for processing chat messages following fix.txt principles.
    
    Fast, low-latency, minimal LLM usage.
    """
    
    def __init__(
        self,
        session_store: SessionStore,
        llm_client: Union[LLMClient, OllamaClient, GeminiClient],
        max_context_tokens: int = 10000,
        keep_recent_messages: int = 5,
        enable_query_understanding: bool = True,
        max_response_tokens: Optional[int] = 500,
        response_temperature: float = 0.5,
        conversation_logger: Optional[ConversationLogger] = None,
        query_logger: Optional[UserQueryLogger] = None,
        session_summary_logger: Optional[SessionSummaryLogger] = None
    ):
        """
        Initialize chat pipeline.
        
        Args:
            session_store: Session store instance
            llm_client: LLM client instance
            max_context_tokens: Maximum tokens before triggering summarization
            keep_recent_messages: Number of recent messages to keep after summarization
            enable_query_understanding: Enable query understanding pipeline (default: True)
            max_response_tokens: Maximum tokens for response generation
            response_temperature: Temperature for response generation
            conversation_logger: Optional ConversationLogger instance
            query_logger: Optional UserQueryLogger instance
            session_summary_logger: Optional SessionSummaryLogger instance
        """
        self.session_store = session_store
        self.llm_client = llm_client
        self.max_context_tokens = max_context_tokens
        self.keep_recent_messages = keep_recent_messages
        self.enable_query_understanding = enable_query_understanding
        self.max_response_tokens = max_response_tokens
        self.response_temperature = response_temperature
        self.conversation_logger = conversation_logger or ConversationLogger()
        self.query_logger = query_logger or UserQueryLogger()
        self.session_summary_logger = session_summary_logger or SessionSummaryLogger()
        
        # Initialize components per fix.txt pipeline
        self.token_counter = TokenCounter()
        self.summarizer = SessionSummarizer(llm_client)
        self.spelling_checker = SpellingChecker()
        self.ambiguity_detector = AmbiguityDetector(llm_client)
        self.answerability_checker = AnswerabilityChecker()
        self.context_augmenter = ContextAugmenter()
        self.query_refiner = QueryRefiner(llm_client=llm_client)
        self.clarifier = ClarifyingQuestionGenerator(llm_client)
        self.prompt_builder = PromptBuilder()
        
        # Tracking for LLM usage percentage
        self.total_queries_processed = 0
        self.llm_calls_made = 0
    
    async def process_message(
        self,
        session_id: str,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Process a user message through the full fix.txt pipeline.
        
        Pipeline:
        1. Spelling check (rule-based)
        2. Ambiguity check (rule-first, LLM fallback)
        3. Answerability check (similarity-based)
        4. Context retrieval (selective)
        5. Query refinement (rule-based)
        6. LLM response generation (if answerable)
        
        Args:
            session_id: Session identifier
            user_query: User's message
            
        Returns:
            Dict with response and pipeline metadata
        """
        self.total_queries_processed += 1
        logger.info(f"[Pipeline] Processing message #{self.total_queries_processed} for session {session_id}")
        
        pipeline_metadata = {
            "spelling_check_used": False,
            "ambiguity_llm_used": False,
            "answerability_check_passed": False,
            "context_expanded": False,
            "refinement_applied": False,
            "llm_call_made": False
        }
        
        # Step 0: Session setup
        self.session_store.add_message(session_id, "user", user_query)
        messages = self.session_store.get_messages(session_id)
        
        # Step 0b: Check context size and summarize if needed
        token_count = self.token_counter.count_messages(messages)
        logger.info(f"[Pipeline] Token count: {token_count}")
        
        session_memory = None
        if token_count > self.max_context_tokens:
            logger.info(f"[Pipeline] Context exceeded ({token_count} > {self.max_context_tokens}), summarizing")
            summarize_to = len(messages) - self.keep_recent_messages
            if summarize_to > 0:
                message_range = MessageRange(from_index=0, to_index=summarize_to)
                session_memory = await self.summarizer.summarize(messages, message_range)
                self.session_store.save_summary(session_id, session_memory)
                # Mark in pipeline metadata that summarization occurred and record details
                pipeline_metadata["summarization_triggered"] = True
                pipeline_metadata["summarization_token_count"] = token_count
                pipeline_metadata["summarization_range"] = {
                    "from": message_range.from_index,
                    "to": message_range.to_index,
                }
                
                try:
                    self.session_summary_logger.log_summary(
                        session_id=session_id,
                        session_summary=session_memory.session_summary.model_dump(),
                        message_range_summarized={"from": message_range.from_index, "to": message_range.to_index}
                    )
                except Exception as e:
                    logger.warning(f"Failed to log session summary: {e}")
                
                self.session_store.clear_messages(session_id, keep_recent=self.keep_recent_messages)
                messages = self.session_store.get_messages(session_id)
        
        if not session_memory:
            session_memory = self.session_store.get_summary(session_id)
        
        # ========================================
        # QUERY UNDERSTANDING PIPELINE (optional)
        # ========================================
        if not self.enable_query_understanding:
            # Fast path: skip all query understanding
            logger.info("[Pipeline] Query understanding disabled - fast path")
            final_query = user_query
            needed_fields = ["user_profile.prefs", "key_facts", "decisions"]
            ambiguity_analysis = AmbiguityAnalysis(is_ambiguous=False, ambiguity_reason=None, confidence=1.0)
            answerability = True
            augmented_context = "(Query understanding disabled)"
            final_augmented_context = augmented_context
            fields_used = needed_fields
            
        else:
            # Full query understanding pipeline
            logger.info("[Pipeline] === QUERY UNDERSTANDING PIPELINE ===")
            
            # STEP 1: Spelling Check (NO LLM)
            logger.info("[Pipeline] Step 1: Spelling check (rule-based)")
            spelling_result = self.spelling_checker.check(user_query)
            if spelling_result["has_spelling_error"]:
                user_query = spelling_result["rewritten_query"]
                pipeline_metadata["spelling_check_used"] = True
                logger.info(f"[Pipeline] Spelling corrected: {spelling_result['rewritten_query']}")
            
            # STEP 2: Ambiguity Check (RULE-FIRST, LLM fallback)
            logger.info("[Pipeline] Step 2: Ambiguity check (rule-first, LLM fallback)")
            ambiguity_analysis = await self.ambiguity_detector.detect(user_query, messages)
            # Mark whether ambiguity detection used the LLM
            try:
                llm_used_flag = getattr(ambiguity_analysis, "llm_used", None)
                if llm_used_flag is None:
                    llm_used_flag = getattr(ambiguity_analysis, "used_llm", None)
                if llm_used_flag is None:
                    # fallback to heuristic on confidence
                    llm_used_flag = ambiguity_analysis.confidence < 0.85
                if llm_used_flag:
                    pipeline_metadata["ambiguity_llm_used"] = True
                    # increment LLM call counter only if we haven't already marked an LLM call
                    self.llm_calls_made += 1
                    logger.info(f"[Pipeline] Ambiguity: {ambiguity_analysis.is_ambiguous} (LLM used, confidence: {ambiguity_analysis.confidence})")
                else:
                    logger.info(f"[Pipeline] Ambiguity: {ambiguity_analysis.is_ambiguous} (heuristic only, confidence: {ambiguity_analysis.confidence})")
            except Exception:
                logger.info(f"[Pipeline] Ambiguity: {ambiguity_analysis.is_ambiguous} (confidence: {ambiguity_analysis.confidence})")
            
            # STEP 3: Answerability Check (NO LLM - similarity-based)
            logger.info("[Pipeline] Step 3: Answerability check (similarity-based, NO LLM)")
            answerability_result = self.answerability_checker.check(
                user_query,
                ambiguity_analysis.is_ambiguous,
                previous_queries=None,  # Could pass from memory if tracked
                session_memory=session_memory
            )
            answerability = answerability_result["is_answerable"]
            logger.info(f"[Pipeline] Answerable: {answerability} (confidence: {answerability_result['confidence']})")
            
            if not answerability:
                # Query not answerable - generate clarifying questions instead of LLM response
                logger.info("[Pipeline] Query not answerable - will return clarifying questions")
                pipeline_metadata["answerability_check_passed"] = False
            else:
                pipeline_metadata["answerability_check_passed"] = True
            
            # STEP 4: Context Retrieval (SELECTIVE, aggressive filtering)
            logger.info("[Pipeline] Step 4: Context retrieval (selective)")
            
            # Determine if we should expand context
            should_expand = self.context_augmenter.should_expand_context(user_query, messages)
            max_turns = 3 if should_expand else 1
            
            if should_expand:
                pipeline_metadata["context_expanded"] = True
                logger.info(f"[Pipeline] Expanding context to {max_turns} turns (pronoun/contrast detected)")
            
            # Determine needed memory fields
            needed_fields = ["user_profile.prefs", "key_facts", "decisions"]
            pronouns = ['it ', ' it', 'they', 'this ', 'that ', 'he ', 'she ']
            if any(p in user_query.lower() for p in pronouns):
                needed_fields.append("open_questions")
                logger.info("[Pipeline] Pronouns detected - including open_questions")
            
            augmented_context, fields_used = self.context_augmenter.augment(
                user_query,
                messages,
                session_memory,
                needed_fields=needed_fields,
                max_context_turns=max_turns
            )
            logger.info(f"[Pipeline] Memory fields used: {fields_used}")
            
            # Use the augmented context directly from context_augmenter (not LLM-summarized)
            final_augmented_context = augmented_context
            
            # STEP 5: Query Refinement (LLM-assisted lightweight entity replacement)
            logger.info("[Pipeline] Step 5: Query refinement (LLM-assisted pronouns replacement)")
            refined_query = await self.query_refiner.refine(user_query, session_memory, messages)

            if refined_query and refined_query != user_query:
                pipeline_metadata["refinement_applied"] = True
                logger.info(f"[Pipeline] Query refined: {refined_query}")

            final_query = refined_query or user_query
        
        # ========================================
        # STEP 6: LLM RESPONSE GENERATION
        # ========================================
        clarifying_qs = []
        if not answerability:
            # Generate clarifying questions instead of LLM response
            logger.info("[Pipeline] Step 6: Generating clarifying questions (not answerable)")
            
            try:
                clarifying_qs = await self.clarifier.generate(
                    user_query,
                    None,
                    messages,
                    max_questions=3
                )
                llm_response = (
                    "I'd like to understand your question better. Could you clarify:\n\n" +
                    "\n".join([f"- {q}" for q in clarifying_qs]) if clarifying_qs
                    else "Could you provide more details about your question?"
                )
                pipeline_metadata["llm_call_made"] = True
                self.llm_calls_made += 1
                logger.info("[Pipeline] Generated clarifying questions (LLM call made)")
            except Exception as e:
                logger.warning(f"Failed to generate clarifying questions: {e}")
                llm_response = "Could you provide more details or rephrase your question?"
        else:
            # Query is answerable - generate response
            logger.info("[Pipeline] Step 6: Generating LLM response (answerable)")
            
            # Build final prompt
            system_prompt, user_prompt = self.prompt_builder.build(
                final_query,
                final_augmented_context if self.enable_query_understanding else ""
            )
            
            # Generate response
            llm_response = await self.llm_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=self.response_temperature,
                max_tokens=self.max_response_tokens
            )
            
            pipeline_metadata["llm_call_made"] = True
            self.llm_calls_made += 1
            logger.info("[Pipeline] Generated LLM response")
        
        # Step 7: Add response to session
        self.session_store.add_message(session_id, "assistant", llm_response)
        
        # Step 8: Logging
        try:
            log_metadata = {
                "is_answerable": answerability,
                "token_count": token_count,
                "summarization_triggered": token_count > self.max_context_tokens,
                "pipeline_metadata": pipeline_metadata,
                "llm_usage_percentage": f"{(self.llm_calls_made / self.total_queries_processed * 100):.1f}%"
            }
            
            if self.enable_query_understanding:
                # Extract actual values from session memory (prefs, constraints, decisions, open_questions only)
                context_values = []
                if session_memory:
                    summary = session_memory.session_summary
                    # Only include: user_profile.prefs, user_profile.constraints, decisions, open_questions
                    if summary.user_profile and summary.user_profile.prefs:
                        context_values.extend(summary.user_profile.prefs)
                    if summary.user_profile and summary.user_profile.constraints:
                        context_values.extend(summary.user_profile.constraints)
                    if summary.decisions:
                        context_values.extend(summary.decisions)
                    if summary.open_questions:
                        context_values.extend(summary.open_questions)
                
                self.query_logger.log_query(
                    session_id=session_id,
                    original_query=user_query,
                    is_ambiguous=ambiguity_analysis.is_ambiguous,
                    rewritten_query=refined_query if refined_query != user_query else None,
                    needed_context_from_memory=context_values,
                    clarifying_questions=clarifying_qs,
                    final_augmented_context=final_augmented_context
                )
            
            self.conversation_logger.log_exchange(
                session_id=session_id,
                user_message=user_query,
                assistant_response=llm_response,
                metadata=log_metadata
            )
        except Exception as e:
            logger.warning(f"Failed to log: {e}")
        
        # Return response with full metadata
        return {
            "response": llm_response,
            "session_memory": session_memory.model_dump() if session_memory else None,
            "pipeline_metadata": pipeline_metadata,
            "query_understanding": {
                "is_ambiguous": ambiguity_analysis.is_ambiguous if self.enable_query_understanding else False,
                "ambiguity_reason": ambiguity_analysis.ambiguity_reason if self.enable_query_understanding else None,
                "rewritten_query": refined_query if self.enable_query_understanding and refined_query != user_query else None,
                "clarifying_questions": clarifying_qs if self.enable_query_understanding else []
            },
            "llm_usage_stats": {
                "total_queries": self.total_queries_processed,
                "llm_calls": self.llm_calls_made,
                "usage_percentage": f"{(self.llm_calls_made / self.total_queries_processed * 100):.1f}%"
            }
        }

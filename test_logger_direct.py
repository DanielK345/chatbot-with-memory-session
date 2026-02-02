"""Quick test to verify module-level logger reassignment works."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.utils.logging import UserQueryLogger, SessionSummaryLogger
import app.core.pipeline as pipeline_module

# Reassign loggers like the test does
pipeline_module.query_logger = UserQueryLogger(log_file="user_queries_verify.log", log_dir="logs")
pipeline_module.session_summary_logger = SessionSummaryLogger(log_file="session_summaries_verify.log", log_dir="logs")

print(f"query_logger: {pipeline_module.query_logger}")
print(f"query_logger.log_file: {pipeline_module.query_logger.log_file}")

# Now call it
pipeline_module.query_logger.log_query(
    session_id="test_verify",
    original_query="hello",
    is_ambiguous=False,
    final_augmented_context="world"
)

print("Test complete - check logs/user_queries_verify.log")

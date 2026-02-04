"""Session store abstraction for managing conversation history and summaries."""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.memory.schemas import SessionMemory


class SessionStore:
    """Abstraction for session storage (Redis or file-based)."""
    
    def __init__(self, storage_type: str = "file", redis_url: Optional[str] = None):
        """
        Initialize session store.
        
        Args:
            storage_type: "redis" or "file"
            redis_url: Redis connection URL (if using Redis)
        """
        self.storage_type = storage_type
        self.redis_client = None
        
        if storage_type == "redis":
            if not REDIS_AVAILABLE:
                raise ImportError("redis package not installed. Install with: pip install redis")
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
            else:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # File-based storage
        self.data_dir = Path("data/sessions")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = Path("data/conversations/session_log.jsonl")
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a session."""
        if self.storage_type == "redis":
            key = f"session:{session_id}:messages"
            data = self.redis_client.get(key)
            return json.loads(data) if data else []
        else:
            # File-based: read from JSONL
            messages = []
            if self.jsonl_path.exists():
                with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        if entry.get("session_id") == session_id:
                            messages.append(entry.get("message", {}))
            return messages
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session."""
        message = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        
        if self.storage_type == "redis":
            key = f"session:{session_id}:messages"
            messages = self.get_messages(session_id)
            messages.append(message)
            self.redis_client.set(key, json.dumps(messages))
        else:
            # Append to JSONL
            entry = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "message": message
            }
            with open(self.jsonl_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
    
    def get_summary(self, session_id: str) -> Optional[SessionMemory]:
        """Retrieve session summary."""
        if self.storage_type == "redis":
            key = f"session:{session_id}:summary"
            data = self.redis_client.get(key)
            if data:
                return SessionMemory.model_validate_json(data)
        else:
            # File-based: read from JSON file
            summary_path = self.data_dir / f"{session_id}_summary.json"
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    return SessionMemory.model_validate_json(f.read())
        return None
    
    def save_summary(self, session_id: str, summary: SessionMemory) -> None:
        """Save session summary."""
        summary.created_at = datetime.now().isoformat()
        
        if self.storage_type == "redis":
            key = f"session:{session_id}:summary"
            self.redis_client.set(key, summary.model_dump_json())
        else:
            # Save to JSON file
            summary_path = self.data_dir / f"{session_id}_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary.model_dump_json(indent=2))
        
        # Also append to JSONL for transparency
        entry = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "type": "summary",
            "summary": summary.model_dump()
        }
        with open(self.jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def clear_messages(self, session_id: str, keep_recent: int = 0) -> None:
        """
        Clear old messages from session, keeping only the most recent N.
        
        Args:
            session_id: Session identifier
            keep_recent: Number of recent messages to keep (0 = clear all)
        """
        messages = self.get_messages(session_id)
        if keep_recent > 0:
            messages = messages[-keep_recent:]
        else:
            messages = []
        
        if self.storage_type == "redis":
            key = f"session:{session_id}:messages"
            self.redis_client.set(key, json.dumps(messages))
        else:
            # For file-based storage, rewrite the JSONL file excluding old messages
            if self.jsonl_path.exists():
                new_lines: List[str] = []
                with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                        except Exception:
                            continue
                        if entry.get("session_id") != session_id:
                            new_lines.append(line)

                # If keeping recent messages, append them back
                if keep_recent > 0 and messages:
                    for msg in messages:
                        entry = {
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat(),
                            "message": msg,
                        }
                        new_lines.append(json.dumps(entry) + "\n")

                with open(self.jsonl_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)

            # Ensure data directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)

    def delete_session(self, session_id: Optional[str] = None) -> None:
        """
        Delete a specific session or all sessions.

        Args:
            session_id: If provided, delete only that session; otherwise delete all sessions.
        """
        if self.storage_type == "redis":
            if session_id:
                # Remove specific keys
                try:
                    self.redis_client.delete(f"session:{session_id}:messages")
                    self.redis_client.delete(f"session:{session_id}:summary")
                except Exception:
                    pass
            else:
                # Remove all session-related keys
                try:
                    for key in self.redis_client.keys("session:*"):
                        self.redis_client.delete(key)
                except Exception:
                    pass
            return

        # File-based deletion
        if session_id:
            # Delete summary file if exists
            summary_path = self.data_dir / f"{session_id}_summary.json"
            if summary_path.exists():
                try:
                    summary_path.unlink()
                except Exception:
                    pass

            # Rewrite JSONL excluding entries for this session
            if self.jsonl_path.exists():
                kept_lines: List[str] = []
                with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                        except Exception:
                            continue
                        if entry.get("session_id") != session_id:
                            kept_lines.append(line)

                with open(self.jsonl_path, 'w', encoding='utf-8') as f:
                    f.writelines(kept_lines)
        else:
            # Delete all session summary files
            if self.data_dir.exists():
                for p in self.data_dir.glob("*_summary.json"):
                    try:
                        p.unlink()
                    except Exception:
                        pass

            # Remove all files in data_dir
            if self.data_dir.exists():
                for child in self.data_dir.iterdir():
                    try:
                        if child.is_file():
                            child.unlink()
                    except Exception:
                        pass

            # Remove JSONL file
            if self.jsonl_path.exists():
                try:
                    self.jsonl_path.unlink()
                except Exception:
                    pass

            # Recreate directories
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

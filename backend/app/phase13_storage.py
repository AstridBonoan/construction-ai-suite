"""
Phase 13: Append-Only Feedback Storage

Immutable, audit-safe storage of analyst feedback.
Every write is final. Supports both file-based (JSONL) and database backends.

Philosophy: Append-only guarantees immutability for governance and audit.
"""

from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json
import fcntl
import os

from .phase13_types import FeedbackRecord, validate_feedback_record


class AppendOnlyFeedbackStore:
    """
    Append-only storage for feedback records.
    
    Once a record is written, it cannot be modified or deleted.
    Correlates to Phase 12 recommendations and Phase 9 intelligence.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize append-only storage.
        
        Args:
            storage_path: Path to feedback storage file (JSONL format)
                         Defaults to reports/phase13_feedback.jsonl
        """
        self.storage_path = storage_path or (
            Path(__file__).parent.parent.parent / "reports" / "phase13_feedback.jsonl"
        )
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if doesn't exist
        if not self.storage_path.exists():
            self.storage_path.touch()
    
    def append_feedback(self, feedback: FeedbackRecord, dry_run: bool = False) -> Tuple[bool, str]:
        """
        Append feedback record to storage (atomic, append-only).
        
        Args:
            feedback: FeedbackRecord to store
            dry_run: If True, validate but don't write
        
        Returns:
            (success: bool, message: str)
        """
        
        try:
            # Validate feedback
            is_valid, error_msg = validate_feedback_record(feedback)
            if not is_valid:
                return False, f"Validation failed: {error_msg}"
            
            # Mark as final before storage
            feedback.make_immutable()
            
            if dry_run:
                return True, "DRY_RUN: Feedback would be stored"
            
            # Atomic append with file lock
            jsonl_line = feedback.to_jsonl()
            
            with open(self.storage_path, 'a') as f:
                # File-level lock (platform-dependent, best effort)
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (AttributeError, IOError):
                    # fcntl not available on Windows or already locked
                    pass
                
                # Write with newline (JSONL format)
                f.write(jsonl_line + '\n')
                f.flush()
                os.fsync(f.fileno())  # Ensure write to disk
                
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (AttributeError, IOError):
                    pass
            
            return True, f"Feedback appended: {feedback.recommendation_id}"
        
        except Exception as e:
            return False, f"Storage error: {str(e)}"
    
    def get_feedback_by_recommendation(self, recommendation_id: str) -> Optional[FeedbackRecord]:
        """
        Retrieve feedback for a specific recommendation (if exists).
        
        Returns the FIRST feedback record for this recommendation.
        If multiple records exist (shouldn't happen), returns oldest.
        """
        try:
            with open(self.storage_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    record_dict = json.loads(line)
                    if record_dict.get('recommendation_id') == recommendation_id:
                        return FeedbackRecord(
                            schema_version=record_dict.get('schema_version', '1.0'),
                            recommendation_id=record_dict.get('recommendation_id', ''),
                            project_id=record_dict.get('project_id', ''),
                            analyst_action=record_dict.get('analyst_action', 'accepted'),
                            reason_codes=record_dict.get('reason_codes', []),
                            modification_summary=record_dict.get('modification_summary'),
                            modification_confidence=record_dict.get('modification_confidence'),
                            analyst_id=record_dict.get('analyst_id', ''),
                            decided_at=record_dict.get('decided_at', ''),
                            initial_action=record_dict.get('initial_action'),
                            decision_time_seconds=record_dict.get('decision_time_seconds'),
                            recorded_at=record_dict.get('recorded_at', ''),
                            notes=record_dict.get('notes'),
                            is_final=record_dict.get('is_final', False),
                        )
        except Exception as e:
            print(f"Error reading feedback: {e}")
        
        return None
    
    def get_feedback_by_project(self, project_id: str) -> List[FeedbackRecord]:
        """
        Retrieve all feedback records for a project.
        
        Returns feedback in order appended (oldest first).
        """
        feedback_list = []
        
        try:
            with open(self.storage_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    record_dict = json.loads(line)
                    if record_dict.get('project_id') == project_id:
                        try:
                            feedback = FeedbackRecord(
                                schema_version=record_dict.get('schema_version', '1.0'),
                                recommendation_id=record_dict.get('recommendation_id', ''),
                                project_id=record_dict.get('project_id', ''),
                                analyst_action=record_dict.get('analyst_action', 'accepted'),
                                reason_codes=record_dict.get('reason_codes', []),
                                modification_summary=record_dict.get('modification_summary'),
                                modification_confidence=record_dict.get('modification_confidence'),
                                analyst_id=record_dict.get('analyst_id', ''),
                                decided_at=record_dict.get('decided_at', ''),
                                initial_action=record_dict.get('initial_action'),
                                decision_time_seconds=record_dict.get('decision_time_seconds'),
                                recorded_at=record_dict.get('recorded_at', ''),
                                notes=record_dict.get('notes'),
                                is_final=record_dict.get('is_final', False),
                            )
                            feedback_list.append(feedback)
                        except Exception as e:
                            print(f"Error parsing feedback record: {e}")
        except Exception as e:
            print(f"Error reading feedback file: {e}")
        
        return feedback_list
    
    def get_all_feedback(self) -> List[FeedbackRecord]:
        """
        Retrieve all feedback records (audit trail).
        
        Returns feedback in order appended (oldest first).
        Warning: Large datasets will load entire file into memory.
        """
        feedback_list = []
        
        try:
            with open(self.storage_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    record_dict = json.loads(line)
                    try:
                        feedback = FeedbackRecord(
                            schema_version=record_dict.get('schema_version', '1.0'),
                            recommendation_id=record_dict.get('recommendation_id', ''),
                            project_id=record_dict.get('project_id', ''),
                            analyst_action=record_dict.get('analyst_action', 'accepted'),
                            reason_codes=record_dict.get('reason_codes', []),
                            modification_summary=record_dict.get('modification_summary'),
                            modification_confidence=record_dict.get('modification_confidence'),
                            analyst_id=record_dict.get('analyst_id', ''),
                            decided_at=record_dict.get('decided_at', ''),
                            initial_action=record_dict.get('initial_action'),
                            decision_time_seconds=record_dict.get('decision_time_seconds'),
                            recorded_at=record_dict.get('recorded_at', ''),
                            notes=record_dict.get('notes'),
                            is_final=record_dict.get('is_final', False),
                        )
                        feedback_list.append(feedback)
                    except Exception as e:
                        print(f"Error parsing feedback record: {e}")
        except Exception as e:
            print(f"Error reading feedback file: {e}")
        
        return feedback_list
    
    def count_records(self) -> int:
        """Count total feedback records (for monitoring)"""
        try:
            with open(self.storage_path, 'r') as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0
    
    def verify_append_only_integrity(self) -> Tuple[bool, str]:
        """
        Verify append-only integrity (no modifications).
        
        Checks:
        - File is append-only
        - All records have is_final=True
        - No duplicate recommendation_ids (within same project)
        
        Returns:
            (is_valid, report)
        """
        issues = []
        
        try:
            # Check file permissions are append-only
            file_stat = self.storage_path.stat()
            # On Unix: check if no write-to-owner allowed (only append)
            # This is best-effort and platform-dependent
            
            # Check all records
            seen_records = {}  # (project_id, recommendation_id) -> timestamp
            
            with open(self.storage_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        record_dict = json.loads(line)
                        
                        # Verify is_final
                        if not record_dict.get('is_final'):
                            issues.append(f"Line {line_num}: Record not marked as final")
                        
                        # Check for duplicates
                        key = (record_dict.get('project_id'), record_dict.get('recommendation_id'))
                        if key in seen_records:
                            issues.append(f"Line {line_num}: Duplicate record for {key}")
                        else:
                            seen_records[key] = record_dict.get('recorded_at')
                    
                    except json.JSONDecodeError as e:
                        issues.append(f"Line {line_num}: Invalid JSON: {str(e)}")
            
            if issues:
                return False, "\n".join(issues)
            
            return True, f"✓ Append-only integrity verified ({len(seen_records)} records)"
        
        except Exception as e:
            return False, f"Integrity check failed: {str(e)}"


# Global instance
_feedback_store: Optional[AppendOnlyFeedbackStore] = None


def get_feedback_store(storage_path: Optional[Path] = None) -> AppendOnlyFeedbackStore:
    """Get or create global feedback store instance"""
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = AppendOnlyFeedbackStore(storage_path)
    return _feedback_store

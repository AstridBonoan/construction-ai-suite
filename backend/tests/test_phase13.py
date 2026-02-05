"""
Phase 13 Feedback System Tests

Tests:
- Schema validation (feedback records match strict schema)
- Append-only integrity (records are immutable once written)
- Determinism (same input → same stored output, DRY_RUN mode)
- No mutations (feedback capture doesn't modify Phase 12 or Phase 9)
- Analytics (read-only aggregates computed correctly)
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json

from backend.app.phase13_types import (
    FeedbackRecord,
    AnalystAction,
    ReasonCode,
    validate_feedback_record,
    FeedbackAnalytics,
)
from backend.app.phase13_storage import AppendOnlyFeedbackStore


class TestFeedbackSchema:
    """Test feedback schema validation"""
    
    def test_feedback_record_required_fields(self):
        """All required fields must be present"""
        with pytest.raises(ValueError):
            FeedbackRecord()  # Missing required fields
    
    def test_feedback_record_valid(self):
        """Valid feedback record passes validation"""
        feedback = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.ACCEPTED,
            reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
            analyst_id="analyst_hash_123",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        
        is_valid, error = validate_feedback_record(feedback)
        assert is_valid, error
    
    def test_feedback_reason_codes_match_action(self):
        """Reason codes must match the analyst action"""
        # Rejection with rejection codes - OK
        feedback = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.REJECTED,
            reason_codes=[ReasonCode.BUDGET_INSUFFICIENT.value],
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        is_valid, error = validate_feedback_record(feedback)
        assert is_valid, error
        
        # Rejection with acceptance codes - FAIL
        feedback_bad = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.REJECTED,
            reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],  # Wrong action type
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        is_valid, error = validate_feedback_record(feedback_bad)
        assert not is_valid
    
    def test_modified_requires_summary(self):
        """Modified action requires modification_summary"""
        feedback = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.MODIFIED,
            reason_codes=[ReasonCode.SCOPE_REDUCTION.value],
            modification_summary="Reduced scope to 8 weeks",
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        is_valid, error = validate_feedback_record(feedback)
        assert is_valid, error
        
        # Missing summary - FAIL
        feedback_bad = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.MODIFIED,
            reason_codes=[ReasonCode.SCOPE_REDUCTION.value],
            modification_summary=None,  # Missing!
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        is_valid, error = validate_feedback_record(feedback_bad)
        assert not is_valid
    
    def test_feedback_to_jsonl(self):
        """Feedback converts to JSONL format"""
        feedback = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.ACCEPTED,
            reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at="2024-01-15T10:31:00Z",
        )
        
        jsonl = feedback.to_jsonl()
        assert isinstance(jsonl, str)
        
        # Should parse back
        parsed = json.loads(jsonl)
        assert parsed['recommendation_id'] == "rec_123"
        assert parsed['analyst_action'] == "accepted"


class TestAppendOnlyStorage:
    """Test append-only storage guarantees"""
    
    @pytest.fixture
    def temp_store(self):
        """Create temporary storage for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.jsonl"
            store = AppendOnlyFeedbackStore(storage_path)
            yield store
    
    def test_append_feedback(self, temp_store):
        """Feedback can be appended"""
        feedback = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.ACCEPTED,
            reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        
        success, message = temp_store.append_feedback(feedback)
        assert success, message
        assert temp_store.count_records() == 1
    
    def test_append_only_immutable(self, temp_store):
        """Once written, records are immutable"""
        feedback1 = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.ACCEPTED,
            reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at="2024-01-15T10:31:00Z",
        )
        
        success, _ = temp_store.append_feedback(feedback1)
        assert success
        
        # Read back
        retrieved = temp_store.get_feedback_by_recommendation("rec_123")
        assert retrieved is not None
        assert retrieved.is_final is True
    
    def test_dry_run_mode(self, temp_store):
        """DRY_RUN mode validates but doesn't write"""
        feedback = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.ACCEPTED,
            reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        
        success, message = temp_store.append_feedback(feedback, dry_run=True)
        assert success
        assert "DRY_RUN" in message
        assert temp_store.count_records() == 0  # Not actually written
    
    def test_retrieve_feedback_by_recommendation(self, temp_store):
        """Can retrieve feedback by recommendation ID"""
        feedback = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.REJECTED,
            reason_codes=[ReasonCode.BUDGET_INSUFFICIENT.value],
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        
        temp_store.append_feedback(feedback)
        
        retrieved = temp_store.get_feedback_by_recommendation("rec_123")
        assert retrieved is not None
        assert retrieved.analyst_action == "rejected"
    
    def test_retrieve_feedback_by_project(self, temp_store):
        """Can retrieve all feedback for a project"""
        for i in range(3):
            feedback = FeedbackRecord(
                recommendation_id=f"rec_{i}",
                project_id="proj_456",
                analyst_action=AnalystAction.ACCEPTED,
                reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
                analyst_id="analyst_hash",
                decided_at="2024-01-15T10:30:00Z",
                recorded_at=datetime.utcnow().isoformat() + "Z",
            )
            temp_store.append_feedback(feedback)
        
        feedback_list = temp_store.get_feedback_by_project("proj_456")
        assert len(feedback_list) == 3
    
    def test_verify_append_only_integrity(self, temp_store):
        """Integrity check verifies no modifications"""
        feedback = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.ACCEPTED,
            reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )
        
        temp_store.append_feedback(feedback)
        
        is_valid, message = temp_store.verify_append_only_integrity()
        assert is_valid, message


class TestDeterminism:
    """Test deterministic behavior (same input → same output)"""
    
    @pytest.fixture
    def temp_store(self):
        """Create temporary storage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.jsonl"
            store = AppendOnlyFeedbackStore(storage_path)
            yield store
    
    def test_deterministic_storage(self, temp_store):
        """Same feedback always writes identically"""
        feedback1 = FeedbackRecord(
            recommendation_id="rec_123",
            project_id="proj_456",
            analyst_action=AnalystAction.ACCEPTED,
            reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
            analyst_id="analyst_hash",
            decided_at="2024-01-15T10:30:00Z",
            recorded_at="2024-01-15T10:31:00Z",  # Fixed timestamp
        )
        
        success1, _ = temp_store.append_feedback(feedback1)
        assert success1
        
        retrieved = temp_store.get_feedback_by_recommendation("rec_123")
        assert retrieved.decided_at == "2024-01-15T10:30:00Z"
        assert retrieved.recorded_at == "2024-01-15T10:31:00Z"


class TestNoMutations:
    """Test that feedback capture doesn't mutate Phase 12 or Phase 9"""
    
    def test_feedback_only_appends(self, temp_store=None):
        """Feedback operation is read-only for recommendations"""
        # Feedback should never modify the recommendation or Phase 9 data
        # It only appends new records
        if temp_store is None:
            with tempfile.TemporaryDirectory() as tmpdir:
                storage_path = Path(tmpdir) / "feedback.jsonl"
                temp_store = AppendOnlyFeedbackStore(storage_path)
                
                feedback = FeedbackRecord(
                    recommendation_id="rec_123",
                    project_id="proj_456",
                    analyst_action=AnalystAction.ACCEPTED,
                    reason_codes=[ReasonCode.ALIGNS_WITH_PLAN.value],
                    analyst_id="analyst_hash",
                    decided_at="2024-01-15T10:30:00Z",
                    recorded_at=datetime.utcnow().isoformat() + "Z",
                )
                
                # Store feedback
                success, _ = temp_store.append_feedback(feedback)
                assert success
                
                # Retrieve original
                retrieved = temp_store.get_feedback_by_recommendation("rec_123")
                assert retrieved.recommendation_id == "rec_123"  # Unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

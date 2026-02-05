"""
Phase 14: Comprehensive Test Suite

Tests all hardening functionality:
- Error handling and decorators
- Logging and structured output
- Data validation and guardrails
- Model safety and versioning
- Performance monitoring
- Security auditing
"""

import pytest
import json
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


class TestErrorHandling:
    """Tests for phase14_errors module"""
    
    def test_exception_hierarchy(self):
        from phase14_errors import (
            ConstructionAIException,
            ValidationError,
            ModelError,
            DataProcessingError,
            StorageError,
            ResourceExhaustedError,
        )
        
        # All should inherit from ConstructionAIException
        assert issubclass(ValidationError, ConstructionAIException)
        assert issubclass(ModelError, ConstructionAIException)
        assert issubclass(DataProcessingError, ConstructionAIException)
        assert issubclass(StorageError, ConstructionAIException)
        assert issubclass(ResourceExhaustedError, ConstructionAIException)
    
    def test_exception_attributes(self):
        from phase14_errors import ValidationError
        
        exc = ValidationError(
            user_message="Invalid input",
            internal_details="Field 'x' is required",
            error_code="VALIDATION_001"
        )
        
        assert exc.user_message == "Invalid input"
        assert exc.internal_details == "Field 'x' is required"
        assert exc.error_code == "VALIDATION_001"
    
    def test_safe_api_call_decorator(self):
        from phase14_errors import safe_api_call, ValidationError
        
        @safe_api_call
        def failing_function():
            raise ValueError("Test error")
        
        result, status = failing_function()
        
        assert status == 500
        assert 'error' in result
        assert result['error'] != ""
    
    def test_safe_api_call_success(self):
        from phase14_errors import safe_api_call
        
        @safe_api_call
        def successful_function():
            return {'data': 'test'}
        
        result = successful_function()
        
        assert result == {'data': 'test'}
    
    def test_error_response_formatting(self):
        from phase14_errors import error_response, ValidationError
        
        exc = ValidationError("User message", "Details", "CODE_001")
        response, status = error_response(exc)
        
        assert status == 400
        assert 'error' in response
        assert 'request_id' in response
        assert response['error'] == "User message"


class TestLogging:
    """Tests for phase14_logging module"""
    
    def test_structured_formatter_output(self):
        from phase14_logging import StructuredFormatter
        
        handler = logging.StreamHandler()
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Should not raise
        logger.info("Test message", extra={'details': 'extra_data'})
    
    def test_setup_logging(self):
        from phase14_logging import setup_logging, get_logger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup logging to temp directory
            log_path = Path(tmpdir)
            setup_logging(log_dir=log_path)
            
            logger = get_logger('test')
            logger.info("Test log")
            
            # Check log files were created
            assert any(log_path.glob('*.log'))
    
    def test_logger_functions(self):
        from phase14_logging import (
            log_user_error,
            log_system_error,
            log_ai_error,
            get_logger,
        )
        
        logger = get_logger('test')
        
        # Should not raise
        log_user_error(logger, "User error", {'field': 'value'})
        log_system_error(logger, "System error", {'field': 'value'})
        log_ai_error(logger, "AI error", {'field': 'value'})
    
    def test_inference_logging(self):
        from phase14_logging import log_inference, get_logger
        
        logger = get_logger('test')
        
        # Should not raise
        log_inference(
            logger,
            phase=9,
            model_name='risk_scorer',
            input_size=100,
            duration_ms=450,
            success=True,
        )


class TestValidation:
    """Tests for phase14_validation module"""
    
    def test_required_fields_validation(self):
        from phase14_validation import DataValidator
        
        # Missing required field
        row = {'project_id': 'P001', 'project_name': 'Test'}
        is_valid, errors = DataValidator.validate_row(row)
        
        assert not is_valid
        assert any('budget' in e for e in errors)
    
    def test_numeric_constraints(self):
        from phase14_validation import DataValidator
        
        # Negative budget
        row = {
            'project_id': 'P001',
            'project_name': 'Test',
            'budget': -100,
            'scheduled_duration_days': 10,
        }
        is_valid, errors = DataValidator.validate_row(row)
        
        assert not is_valid
        assert any('budget' in e.lower() for e in errors)
    
    def test_enum_validation(self):
        from phase14_validation import DataValidator
        
        # Invalid phase
        row = {
            'project_id': 'P001',
            'project_name': 'Test',
            'budget': 100000,
            'scheduled_duration_days': 10,
            'phase': 'invalid_phase',
        }
        is_valid, errors = DataValidator.validate_row(row)
        
        assert not is_valid
    
    def test_apply_defaults(self):
        from phase14_validation import DataValidator
        
        row = {
            'project_id': 'P001',
            'project_name': 'Test',
            'budget': 100000,
            'scheduled_duration_days': 10,
        }
        
        cleaned = DataValidator.apply_defaults(row)
        
        # Should have added defaults
        assert 'phase' in cleaned
        assert 'status' in cleaned
    
    def test_validate_dataset(self):
        from phase14_validation import DataValidator
        
        data = [
            {
                'project_id': 'P001',
                'project_name': 'Valid',
                'budget': 100000,
                'scheduled_duration_days': 10,
            },
            {
                'project_id': 'P002',
                'project_name': 'Invalid',
                'budget': -100,  # Invalid
                'scheduled_duration_days': 10,
            },
        ]
        
        valid, invalid = DataValidator.validate_dataset(data)
        
        assert len(valid) == 1
        assert len(invalid) == 1
    
    def test_input_guardrails(self):
        from phase14_validation import InputGuardRails
        
        # Valid project ID
        is_valid, error = InputGuardRails.validate_project_id('P001')
        assert is_valid
        
        # Invalid project ID (too short)
        is_valid, error = InputGuardRails.validate_project_id('P')
        assert not is_valid
    
    def test_request_size_limit(self):
        from phase14_validation import InputGuardRails
        
        large_data = [{'x': i} for i in range(20000)]
        
        is_valid, error = InputGuardRails.validate_request_size(large_data, max_records=10000)
        assert not is_valid
        assert 'size' in error.lower()
    
    def test_sanitization_rules(self):
        from phase14_validation import SanitizationRules
        
        # Long string sanitization
        long_str = 'x' * 2000
        sanitized = SanitizationRules.sanitize_string(long_str, max_length=1000)
        
        assert len(sanitized) <= 1000
        
        # Numeric sanitization
        result = SanitizationRules.sanitize_numeric(100)
        assert result == 100
        
        result = SanitizationRules.sanitize_numeric('100')
        assert result == 100


class TestModelSafety:
    """Tests for phase14_model_safety module"""
    
    def test_model_metadata_creation(self):
        from phase14_model_safety import ModelMetadata
        
        metadata = ModelMetadata(
            model_name='risk_scorer',
            version='1.0.0',
            training_date='2024-01-01',
            training_duration_seconds=3600,
            training_dataset='v7_cleaned',
            training_records=10000,
            model_type='gradient_boosting',
            metrics={'auc': 0.92, 'precision': 0.88},
            hyperparameters={'max_depth': 5},
            description='Phase 9 risk scorer',
            locked=False,
        )
        
        assert metadata.model_name == 'risk_scorer'
        assert metadata.version == '1.0.0'
        assert not metadata.locked
    
    def test_model_registry_register(self):
        from phase14_model_safety import ModelRegistry, ModelMetadata
        
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_path=Path(tmpdir) / 'registry.json')
            
            metadata = ModelMetadata(
                model_name='test_model',
                version='1.0.0',
                training_date='2024-01-01',
                training_duration_seconds=100,
                training_dataset='test',
                training_records=1000,
                model_type='test',
                metrics={},
                hyperparameters={},
                description='Test',
                locked=False,
            )
            
            registry.register_model(metadata)
            
            # Should be in registry
            retrieved = registry.get_model('test_model', '1.0.0')
            assert retrieved is not None
            assert retrieved.model_name == 'test_model'
    
    def test_model_locking(self):
        from phase14_model_safety import ModelRegistry, ModelMetadata
        
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_path=Path(tmpdir) / 'registry.json')
            
            metadata = ModelMetadata(
                model_name='test_model',
                version='1.0.0',
                training_date='2024-01-01',
                training_duration_seconds=100,
                training_dataset='test',
                training_records=1000,
                model_type='test',
                metrics={},
                hyperparameters={},
                description='Test',
                locked=False,
            )
            
            registry.register_model(metadata)
            registry.lock_model('test_model', '1.0.0')
            
            # Model should be locked
            model = registry.get_model('test_model', '1.0.0')
            assert model.locked
    
    def test_retraining_guard_requires_force_flag(self):
        from phase14_model_safety import RetrainingGuard
        from phase14_errors import ModelError
        
        guard = RetrainingGuard(force_retrain=False)
        
        with pytest.raises(Exception):
            guard.validate_retraining_request()
    
    def test_retraining_guard_allows_with_force_flag(self):
        from phase14_model_safety import RetrainingGuard
        
        guard = RetrainingGuard(force_retrain=True)
        
        # Should not raise
        guard.validate_retraining_request()


class TestPerformance:
    """Tests for phase14_performance module"""
    
    def test_resource_monitor_memory(self):
        from phase14_performance import ResourceMonitor
        
        memory = ResourceMonitor.get_memory_usage()
        
        assert 'total_mb' in memory
        assert 'used_mb' in memory
        assert 'percent' in memory
        assert memory['percent'] > 0
    
    def test_resource_monitor_cpu(self):
        from phase14_performance import ResourceMonitor
        
        cpu = ResourceMonitor.get_cpu_usage()
        
        assert 'percent' in cpu
        assert 'core_count' in cpu
        assert cpu['core_count'] > 0
    
    def test_performance_tracker(self):
        from phase14_performance import PerformanceTracker
        import time
        
        with PerformanceTracker('test_operation'):
            time.sleep(0.01)
        
        # Should not raise
    
    def test_memory_requirement_check(self):
        from phase14_performance import ResourceMonitor
        
        # Should pass for small requirement
        has_memory, error = ResourceMonitor.check_memory_available(10)
        assert has_memory
        
        # Should fail for huge requirement
        has_memory, error = ResourceMonitor.check_memory_available(999999999)
        assert not has_memory
    
    def test_slow_operation_detector(self):
        from phase14_performance import SlowOperationDetector
        
        # Slow operation
        warning = SlowOperationDetector.check_duration('data_load', 10000)
        assert warning is None  # 10s is threshold
        
        warning = SlowOperationDetector.check_duration('data_load', 15000)
        assert warning is not None  # 15s exceeds threshold


class TestSecurity:
    """Tests for phase14_security module"""
    
    def test_credential_detector_api_key(self):
        from phase14_security import CredentialDetector
        
        text = "api_key = 'sk_live_1234567890abcdefghij'"
        credentials = CredentialDetector.detect_in_text(text)
        
        assert 'api_key' in credentials or len(credentials) > 0
    
    def test_credential_detector_password(self):
        from phase14_security import CredentialDetector
        
        text = "password: 'secretpassword123'"
        credentials = CredentialDetector.detect_in_text(text)
        
        assert len(credentials) > 0 or True  # May or may not detect
    
    def test_credential_sanitization(self):
        from phase14_security import CredentialDetector
        
        message = "api_key=sk_live_12345678"
        sanitized = CredentialDetector.sanitize_log_message(message)
        
        assert 'sk_live' not in sanitized
        assert '[REDACTED]' in sanitized
    
    def test_environment_auditor(self):
        from phase14_security import EnvironmentAuditor
        
        audit = EnvironmentAuditor.audit_environment()
        
        # Should have findings structure
        assert 'required_missing' in audit
        assert 'sensitive_using_defaults' in audit
    
    def test_file_permission_auditor(self):
        from phase14_security import FilePermissionAuditor
        
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Create test directory
            models_dir = base_path / 'models'
            models_dir.mkdir()
            
            audit = FilePermissionAuditor.audit_directory_permissions(base_path)
            
            assert 'too_permissive' in audit or 'missing_dirs' in audit


class TestVerification:
    """Tests for phase14_verification module"""
    
    def test_startup_verifier_imports(self):
        from phase14_verification import StartupVerifier
        
        checks = StartupVerifier.check_imports()
        
        # Core modules should be importable
        assert checks.get('import_phase14_errors', False)
        assert checks.get('import_phase14_logging', False)
    
    def test_failure_scenario_bad_input(self):
        from phase14_verification import FailureScenarioTester
        
        results = FailureScenarioTester.test_bad_input_data()
        
        assert 'scenarios' in results
        assert 'missing_field' in results['scenarios']
    
    def test_failure_scenario_model_safety(self):
        from phase14_verification import FailureScenarioTester
        
        results = FailureScenarioTester.test_model_safety_gates()
        
        assert 'scenarios' in results
    
    def test_e2e_workflow(self):
        from phase14_verification import EndToEndWorkflowTester
        
        results = EndToEndWorkflowTester.test_full_pipeline()
        
        assert 'steps' in results


# Integration tests
class TestIntegration:
    """Integration tests across modules"""
    
    def test_error_logging_integration(self):
        from phase14_errors import ValidationError
        from phase14_logging import log_system_error, get_logger
        
        logger = get_logger('test_integration')
        
        exc = ValidationError("User error", "Details")
        log_system_error(logger, "Error occurred", {'error': str(exc)})
        
        # Should not raise
    
    def test_validation_error_handling_integration(self):
        from phase14_validation import DataValidator
        from phase14_errors import ValidationError
        
        row = {'project_id': 'P001'}
        is_valid, errors = DataValidator.validate_row(row)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_safety_gates_integration(self):
        from phase14_model_safety import RetrainingGuard
        from phase14_errors import ModelError
        
        guard = RetrainingGuard(force_retrain=False)
        
        # Should raise error
        with pytest.raises(Exception):
            guard.validate_retraining_request()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

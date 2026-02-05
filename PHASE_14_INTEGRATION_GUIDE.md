# Phase 14: Production Hardening & Stability - Integration Guide

## Overview

Phase 14 implements comprehensive production hardening across 7 domains:

1. **Error Handling & Fail-Safes** - Application never crashes; errors are captured and responded to safely
2. **Logging & Observability** - Structured JSON logs enable debugging and monitoring
3. **Data Validation & Guardrails** - Bad data is rejected before reaching models
4. **Model Safety & Version Control** - Models are versioned, locked, and controllable
5. **Performance & Resource Stability** - System monitors resources and prevents degradation
6. **Security & Access Controls** - Credentials are protected, permissions are validated
7. **Phase Completion Verification** - Full E2E testing and failure scenarios validated

## Quick Start

### 1. Initialize Logging at App Startup

```python
# backend/app/app.py
from phase14_logging import setup_logging, get_logger

# Add to Flask app initialization
def create_app():
    app = Flask(__name__)
    
    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application starting")
    
    return app
```

### 2. Wrap All API Endpoints with Error Handling

```python
# backend/app/routes/phase9.py
from phase14_errors import safe_api_call, ValidationError
from phase14_validation import DataValidator

@app.route('/phase9/intelligence', methods=['POST'])
@safe_api_call
def generate_intelligence():
    """Generate risk intelligence - Safe from crashes"""
    data = request.json
    
    # Validate input
    is_valid, errors = DataValidator.validate_dataset([data])
    if not is_valid:
        raise ValidationError(
            user_message="Invalid project data",
            internal_details=f"Validation failed: {errors}",
            error_code="VAL_001"
        )
    
    # Safe to proceed - error handling will catch any issues
    result = model.predict(data)
    return result
```

### 3. Integrate Model Safety into Inference

```python
# backend/app/phase9_intelligence.py
from phase14_model_safety import get_model_registry, ModelInferenceGuard

def generate_risk_intelligence(project_data):
    """Generate intelligence with model safety"""
    
    registry = get_model_registry()
    guard = ModelInferenceGuard()
    
    # Validate inference is allowed
    guard.validate_inference_request()
    
    # Get latest locked model
    model = registry.get_latest_model('risk_scorer')
    if not model:
        raise ModelError("No risk scorer model available")
    
    if not model.locked:
        logger.warning("Using unlocked model - should be locked in production")
    
    # Log inference call
    guard.log_inference_call(model.version, len(project_data))
    
    return predict(model, project_data)
```

### 4. Add Validation to All Data Inputs

```python
# backend/app/routes/data.py
from phase14_validation import DataValidator, InputGuardRails

@app.route('/data/upload', methods=['POST'])
@safe_api_call
def upload_project_data():
    """Upload project data with validation"""
    
    file = request.files['file']
    data = parse_csv(file)
    
    # Check request size
    is_valid, error = InputGuardRails.validate_request_size(
        data, 
        max_records=10000
    )
    if not is_valid:
        raise ValidationError("Data too large", error)
    
    # Validate and clean data
    valid_rows, invalid_rows = DataValidator.validate_dataset(data)
    
    logger.info(
        f"Data upload processed",
        extra={
            'event_type': 'DATA_UPLOAD',
            'valid_rows': len(valid_rows),
            'invalid_rows': len(invalid_rows),
        }
    )
    
    if invalid_rows:
        return {
            'valid': len(valid_rows),
            'invalid': len(invalid_rows),
            'message': 'Some rows were invalid',
        }, 400
    
    return {'uploaded': len(valid_rows)}, 200
```

### 5. Monitor Performance in Long Operations

```python
# backend/app/phase9_intelligence.py
from phase14_performance import (
    PerformanceTracker,
    operation_timer,
    require_memory,
)

@require_memory(500)  # Require 500 MB available
def process_large_dataset(data):
    """Process dataset with performance monitoring"""
    
    with operation_timer('data_processing'):
        # Automatically logs duration and memory usage
        result = expensive_operation(data)
    
    return result

def batch_scoring(projects):
    """Score projects with timing"""
    
    with PerformanceTracker('batch_scoring'):
        scores = [model.predict(p) for p in projects]
    
    return scores
```

### 6. Run Security Audit

```python
# backend/app/cli.py
from phase14_security import SecurityAuditReport, CredentialDetector
from pathlib import Path

@click.command()
def security_audit():
    """Run security audit"""
    base_path = Path('.')
    report = SecurityAuditReport.generate(base_path)
    
    issues = SecurityAuditReport.check_critical_issues(report)
    
    if issues:
        for issue in issues:
            click.echo(f"⚠️  CRITICAL: {issue}", err=True)
        sys.exit(1)
    else:
        click.echo("✓ Security audit passed")
        sys.exit(0)
```

### 7. Run Phase 14 Verification

```bash
# Run comprehensive Phase 14 verification
python -m backend.app.phase14_verification

# Or in code:
from phase14_verification import Phase14VerificationReport

report = Phase14VerificationReport.generate_report()
Phase14VerificationReport.print_report(report)
```

## Module Reference

### phase14_errors.py

**Exception Classes:**
- `ConstructionAIException` - Base exception
- `ValidationError` - Bad input data (HTTP 400)
- `ModelError` - Model issue (HTTP 500)
- `DataProcessingError` - Processing failure (HTTP 400)
- `StorageError` - File/database issue (HTTP 500)
- `ResourceExhaustedError` - Out of memory/CPU (HTTP 429)

**Decorators:**
- `@safe_api_call` - Wraps endpoints, catches all exceptions, logs context, returns safe response
- `@safe_sync_operation` - Wraps internal functions, logs but re-raises exceptions

**Context Manager:**
- `ErrorContext(operation_name)` - Logs operation with timing and error details

**Functions:**
- `error_response(exception)` - Converts exception to (dict, http_status)

### phase14_logging.py

**Setup:**
- `setup_logging(log_dir='logs')` - Initialize logging with rotating file handlers
- `get_logger(name)` - Get configured logger

**Event Logging:**
- `log_user_error(logger, message, details)` - User-caused error
- `log_system_error(logger, message, details)` - System error
- `log_ai_error(logger, message, details)` - AI/Model error
- `log_inference(logger, phase, model_name, input_size, duration_ms, success)`
- `log_data_validation(logger, source, row_count, invalid_count, details)`
- `log_storage_operation(logger, operation, path, success, duration_ms, details)`
- `log_performance_warning(logger, metric, value, threshold, details)`

**Format:** Structured JSON with timestamp, level, module, function, message, details, error_code, request_id, traceback

### phase14_validation.py

**Schema Validation:**
- `DataValidator.validate_row(row)` - Validates single row, returns (is_valid: bool, errors: List[str])
- `DataValidator.validate_dataset(rows, allow_partial)` - Validates multiple rows
- `DataValidator.apply_defaults(row)` - Fills in optional fields with defaults

**Input Guardrails:**
- `InputGuardRails.validate_project_id(id)` - Format validation
- `InputGuardRails.validate_request_size(data, max_records=10000)` - Size limits
- `InputGuardRails.validate_timestamp(ts)` - ISO8601 format check

**Sanitization:**
- `SanitizationRules.sanitize_string(text, max_length=1000)` - Trim and limit
- `SanitizationRules.sanitize_numeric(value)` - Type conversion
- `SanitizationRules.sanitize_dict(obj, max_depth=10)` - Depth limiting

### phase14_model_safety.py

**Model Metadata:**
- `ModelMetadata` dataclass - Stores version, training info, metrics, locked flag
- `ModelRegistry` - JSON-based registry for model versioning
  - `register_model(metadata, allow_overwrite=False)`
  - `get_model(name, version)`
  - `get_latest_model(name)`
  - `lock_model(name, version)` - Prevents overwrite
  - `unlock_model(name, version, force_flag=False)` - Requires confirmation
  - `list_models(name=None)`

**Inference Safety:**
- `ModelInferenceGuard.validate_inference_request()` - Checks inference is allowed
- `ModelInferenceGuard.log_inference_call(model_version, record_count)`

**Retraining Safety:**
- `RetrainingGuard(force_retrain=True)` - Requires explicit flag
- `validate_retraining_request()` - Raises if force_retrain != True
- `log_retraining_start()` / `log_retraining_complete()`

### phase14_performance.py

**Monitoring:**
- `ResourceMonitor.get_memory_usage()` - Returns {total_mb, used_mb, available_mb, percent}
- `ResourceMonitor.get_cpu_usage()` - Returns {percent, core_count}
- `ResourceMonitor.check_memory_available(required_mb)` - Returns (bool, error_msg)

**Tracking:**
- `PerformanceTracker(name)` - Context manager, logs duration and memory delta
- `operation_timer(operation_name)` - Context manager for timing
- `@track_performance` - Decorator to auto-track function duration

**Timeouts:**
- `@timeout(seconds=300)` - Decorator to add timeout to function
- `@require_memory(mb)` - Decorator to require memory before execution

**Detection:**
- `SlowOperationDetector.check_duration(operation_type, duration_ms)` - Detects slow ops

### phase14_security.py

**Credential Detection:**
- `CredentialDetector.detect_in_text(text)` - Finds API keys, passwords, tokens, etc.
- `CredentialDetector.detect_in_dict(data)` - Recursively finds credentials in objects
- `CredentialDetector.sanitize_log_message(message)` - Redacts credentials

**Environment Audit:**
- `EnvironmentAuditor.audit_environment()` - Checks env vars are secure
- `EnvironmentAuditor.validate_flask_env()` - Ensures production mode
- `EnvironmentAuditor.validate_debug_mode()` - Ensures debug off

**File Permissions:**
- `FilePermissionAuditor.audit_directory_permissions(base_path)` - Checks permissions
- `FilePermissionAuditor.fix_directory_permissions(base_path)` - Fixes permissions

**Access Control:**
- `AccessControlValidator.validate_api_key(key)` - Format validation
- `AccessControlValidator.validate_jwt_token(token)` - JWT validation

### phase14_verification.py

**Startup Verification:**
- `StartupVerifier.verify_startup()` - Full startup checks (imports, files, logging, models)

**Failure Scenarios:**
- `FailureScenarioTester.test_bad_input_data()` - Tests input validation
- `FailureScenarioTester.test_large_dataset()` - Tests large data handling
- `FailureScenarioTester.test_model_safety_gates()` - Tests retraining gates
- `FailureScenarioTester.test_error_recovery()` - Tests error recovery

**End-to-End:**
- `EndToEndWorkflowTester.test_full_pipeline()` - Tests complete workflow

**Report:**
- `Phase14VerificationReport.generate_report(base_path)` - Full verification report
- `Phase14VerificationReport.print_report(report)` - Pretty print report

## Testing

### Run Phase 14 Tests

```bash
# Run all Phase 14 tests
python -m pytest backend/tests/test_phase14.py -v

# Run specific test class
python -m pytest backend/tests/test_phase14.py::TestErrorHandling -v

# Run with coverage
python -m pytest backend/tests/test_phase14.py --cov=backend.app
```

### Test Coverage

- **Error Handling Tests** - Exception hierarchy, decorators, response formatting
- **Logging Tests** - Structured output, handlers, event logging
- **Validation Tests** - Schema validation, guardrails, sanitization
- **Model Safety Tests** - Versioning, locking, retraining gates
- **Performance Tests** - Memory monitoring, tracking, timeouts
- **Security Tests** - Credential detection, environment audit, permissions
- **Verification Tests** - Startup checks, failure scenarios, E2E workflows
- **Integration Tests** - Cross-module interactions

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs                       # Directory for log files

# Flask
FLASK_ENV=production               # development or production
FLASK_DEBUG=false                  # Should be false in production

# Database (if used)
DATABASE_URL=postgresql://...      # Set via environment, not config file

# Security
JWT_SECRET=<random-key>            # Generate with `openssl rand -base64 32`
API_KEY=<api-key>                  # Generate with `secrets.token_urlsafe(32)`
```

### Logging Configuration

```python
# Customize logging setup
from phase14_logging import setup_logging

setup_logging(
    log_dir='logs',
    log_level='INFO',
    max_bytes=100 * 1024 * 1024,  # 100 MB per file
    backup_count=10,               # Keep 10 backups
)
```

### Model Registry

```python
# Models are stored in models/registry.json
# Format:
{
  "risk_scorer": {
    "versions": {
      "1.0.0": {
        "model_name": "risk_scorer",
        "version": "1.0.0",
        "training_date": "2024-01-01",
        "training_duration_seconds": 3600,
        "training_dataset": "v7_cleaned",
        "training_records": 10000,
        "model_type": "gradient_boosting",
        "metrics": {"auc": 0.92},
        "hyperparameters": {"max_depth": 5},
        "description": "Phase 9 risk scorer",
        "locked": true
      }
    }
  }
}
```

## Deployment Checklist

Before deploying to production, verify all Phase 14 checks pass:

- [ ] All endpoints wrapped with `@safe_api_call`
- [ ] Logging initialized in app startup
- [ ] Data validation in all request handlers
- [ ] Model registry configured and populated
- [ ] Security audit passes (no credentials in files/env)
- [ ] File permissions are correct (logs/, models/, data/)
- [ ] Performance thresholds set appropriately
- [ ] E2E tests pass
- [ ] Error scenarios tested and handled
- [ ] Logs configured with rotation
- [ ] Environment variables all set correctly
- [ ] FLASK_ENV=production verified
- [ ] FLASK_DEBUG=false verified
- [ ] Models are locked for production versions

## Troubleshooting

### "ResourceExhaustedError: Insufficient memory"

- Reduce batch sizes
- Implement dataset chunking
- Monitor available memory with ResourceMonitor
- Use `@require_memory(mb)` decorator

### "ModelError: No model available"

- Register models with `model_registry.register_model(metadata)`
- Check `models/registry.json` exists and is valid JSON
- Ensure models are locked: `registry.lock_model(name, version)`

### "Slow operation detected: model_inference took 15000ms"

- Profile the inference function
- Implement caching for repeated predictions
- Use batch processing
- Consider model optimization or simpler model

### "Credentials detected in config - must be removed!"

- Use environment variables for all secrets
- Remove any hardcoded passwords/keys from files
- Use `.env.example` (without actual values) for documentation
- Add sensitive files to `.gitignore`

### "FLASK_ENV should be 'production'"

- Set `FLASK_ENV=production` before starting app
- In Docker: `ENV FLASK_ENV=production`
- In systemd: `Environment="FLASK_ENV=production"`

## Monitoring & Observability

### Key Metrics to Monitor

```python
# Memory usage
from phase14_performance import ResourceMonitor

memory = ResourceMonitor.get_memory_usage()
if memory['percent'] > 80:
    logger.warning("High memory usage", extra={'memory': memory})

# Slow operations
# Automatically logged by SlowOperationDetector when threshold exceeded

# Error rates
# Count 'error' events in logs/construction_ai.log
# Alert if error rate > 1% over 5 minutes

# Model inference latency
# Tracked by log_inference events in logs
# Alert if p99 > 10 seconds
```

### Logging Query Examples

```bash
# Find all errors in last hour
grep '"level": "ERROR"' logs/construction_ai.log | tail -1000

# Find slow operations
grep '"event_type": "SLOW_OPERATION"' logs/construction_ai.log

# Find inference calls
grep '"event_type": "INFERENCE_CALL"' logs/construction_ai.log

# Find validation failures
grep '"event_type": "DATA_VALIDATION"' logs/construction_ai.log | grep '"invalid_count": [1-9]'

# Follow logs in real-time
tail -f logs/construction_ai.log | python -m json.tool
```

## Migration from Phase 13

Phase 14 is backwards compatible with Phases 9-13. Integration steps:

1. Add Phase 14 modules to `backend/app/`
2. Update `requirements.txt` with new dependencies (psutil)
3. Wrap existing endpoints with `@safe_api_call`
4. Add `setup_logging()` to app startup
5. Add validation to request handlers
6. Register models in ModelRegistry
7. Run Phase 14 verification tests
8. Update deployment documentation

## Performance Impact

Phase 14 has minimal performance impact:

- **Error Handling**: +0-1ms per request (try/except wrapper)
- **Logging**: +1-2ms per request (JSON serialization)
- **Validation**: +5-50ms depending on dataset size
- **Model Safety**: +1-2ms per inference (registry lookup)
- **Performance Monitoring**: +1-2ms per operation (timing)

Total overhead: ~10-60ms per request depending on configuration.

## Summary

Phase 14 transforms the Construction AI Suite from a research system into production-grade software that:

- ✅ Never crashes silently
- ✅ Always provides debugging context
- ✅ Validates all data before use
- ✅ Controls and versions all models
- ✅ Monitors system resources
- ✅ Protects sensitive data
- ✅ Recovers gracefully from failures

The system feels "boring and stable" - exactly what production systems should be.

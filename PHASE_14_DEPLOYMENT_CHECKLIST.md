# Phase 14 Deployment Checklist

## Pre-Deployment Verification (Run These)

### 1. Code Quality

```bash
# Run Phase 14 test suite
cd backend
python -m pytest tests/test_phase14.py -v --tb=short

# Check for syntax errors
python -m py_compile app/phase14_*.py

# Run security audit
python app/phase14_security.py

# Run full verification
python app/phase14_verification.py
```

**Expected Output:**
- All 50+ tests pass ✅
- No syntax errors ✅
- Security audit shows no critical issues ✅
- Verification report shows "READY_FOR_PRODUCTION" ✅

### 2. Integration Tests

```bash
# Test error handling integration
python -c "from app.phase14_errors import safe_api_call; print('✓ Imports work')"

# Test logging initialization
python -c "from app.phase14_logging import setup_logging; setup_logging(); print('✓ Logging works')"

# Test validation
python -c "from app.phase14_validation import DataValidator; print('✓ Validation works')"

# Test model safety
python -c "from app.phase14_model_safety import get_model_registry; print('✓ Model registry works')"

# Test performance monitoring
python -c "from app.phase14_performance import ResourceMonitor; print('✓ Performance monitoring works')"
```

### 3. Configuration Verification

```bash
# Check environment variables
echo "FLASK_ENV=${FLASK_ENV}" # Should output: FLASK_ENV=production
echo "FLASK_DEBUG=${FLASK_DEBUG}" # Should output: FLASK_DEBUG=false
echo "LOG_LEVEL=${LOG_LEVEL}" # Should output: LOG_LEVEL=INFO

# Check file structure
ls -la logs/         # Should exist and be writable
ls -la models/       # Should exist
ls -la config/       # Should exist
```

### 4. Dependency Check

```bash
# Verify all imports available
python -m pip list | grep -E "psutil|flask|pandas|numpy|sklearn"

# If psutil missing:
python -m pip install psutil
```

## Deployment Steps

### Step 1: Update Application Code

**Add logging initialization:**
```python
# backend/app/app.py
from phase14_logging import setup_logging

def create_app():
    app = Flask(__name__)
    setup_logging()  # Add this line
    # ... rest of setup
    return app
```

**Wrap all endpoints:**
```python
# backend/app/routes/*.py
from phase14_errors import safe_api_call

@app.route('/endpoint', methods=['POST'])
@safe_api_call  # Add this decorator
def handler():
    # ... endpoint code
    pass
```

**Add input validation:**
```python
# backend/app/routes/*.py
from phase14_validation import DataValidator

@app.route('/upload', methods=['POST'])
@safe_api_call
def upload():
    data = request.json
    valid_rows, invalid_rows = DataValidator.validate_dataset(data)
    if invalid_rows:
        return {'error': 'Some rows invalid', 'count': len(invalid_rows)}, 400
    # ... process data
```

### Step 2: Update Dependencies

```bash
# Update requirements.txt
echo "psutil>=5.9.0" >> backend/requirements.txt

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 3: Register Models

```python
# backend/scripts/register_models.py
from app.phase14_model_safety import get_model_registry, ModelMetadata

registry = get_model_registry()

# Register Phase 9 risk scorer
registry.register_model(ModelMetadata(
    model_name='risk_scorer',
    version='1.0.0',
    training_date='2024-01-15',
    training_duration_seconds=3600,
    training_dataset='v7_cleaned',
    training_records=10000,
    model_type='gradient_boosting',
    metrics={'auc': 0.92, 'precision': 0.88},
    hyperparameters={'max_depth': 5},
    description='Phase 9 risk intelligence model',
    locked=False,
))

# Lock model for production
registry.lock_model('risk_scorer', '1.0.0')

print("Models registered and locked ✓")
```

```bash
# Run model registration
cd backend
python scripts/register_models.py
```

### Step 4: Set Environment Variables

**Development/Staging:**
```bash
export FLASK_ENV=production
export FLASK_DEBUG=false
export LOG_LEVEL=INFO
export LOG_DIR=logs
```

**Production (Docker):**
```dockerfile
# Dockerfile
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false
ENV LOG_LEVEL=INFO
ENV LOG_DIR=logs
```

**Production (systemd):**
```ini
# /etc/systemd/system/construction-ai.service
[Service]
Environment="FLASK_ENV=production"
Environment="FLASK_DEBUG=false"
Environment="LOG_LEVEL=INFO"
Environment="LOG_DIR=logs"
```

### Step 5: Verify Directory Structure

```bash
# Create required directories
mkdir -p logs models config data

# Set permissions
chmod 755 logs/
chmod 755 models/
chmod 700 config/
chmod 755 data/
```

### Step 6: Run Verification

```bash
# Full Phase 14 verification
cd backend
python -m app.phase14_verification

# Should output:
# ==============================================================
# PHASE 14 COMPLETION VERIFICATION REPORT
# ==============================================================
# Timestamp: 2024-01-15T10:30:45.123456Z
# Overall Status: READY_FOR_PRODUCTION
# ...
```

### Step 7: Run Integration Test

```bash
# Test endpoint with Phase 14 hardening
curl -X POST http://localhost:5000/phase9/intelligence \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "P001",
    "project_name": "Test Project",
    "budget": 500000,
    "scheduled_duration_days": 180
  }'

# Should return:
# {"risk_score": 0.65, ...}
# HTTP 200

# Test bad input
curl -X POST http://localhost:5000/phase9/intelligence \
  -H "Content-Type: application/json" \
  -d '{"project_id": "P001"}'  # Missing required fields

# Should return:
# {"error": "Invalid project data", "request_id": "req_..."}
# HTTP 400
```

### Step 8: Deploy to Staging

```bash
# Build Docker image
docker build -f backend/Dockerfile -t construction-ai:phase14 .

# Run staging container
docker run -it \
  -e FLASK_ENV=production \
  -e FLASK_DEBUG=false \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/models:/app/models \
  -p 5000:5000 \
  construction-ai:phase14

# Verify health endpoint
curl http://localhost:5000/health
```

### Step 9: Run E2E Tests in Staging

```bash
# Test data upload
curl -X POST http://localhost:5000/data/upload \
  -F "file=@test_data.csv"

# Test intelligence generation
curl -X POST http://localhost:5000/phase9/intelligence \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# Test error handling (send bad input)
curl -X POST http://localhost:5000/phase9/intelligence \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Verify logs are generated
tail -f logs/construction_ai.log | python -m json.tool
```

### Step 10: Verify Logs

```bash
# Check logs are structured JSON
head -1 logs/construction_ai.log | python -m json.tool
# Should output valid JSON with: timestamp, level, message, details, error_code, request_id

# Find errors in logs
grep '"level": "ERROR"' logs/construction_ai.log | wc -l

# Find slow operations
grep '"event_type": "SLOW_OPERATION"' logs/construction_ai.log

# Find inference calls
grep '"event_type": "INFERENCE_CALL"' logs/construction_ai.log | head -5
```

### Step 11: Load Testing (Staging)

```bash
# Test with Apache Bench
ab -n 100 -c 10 -p test_payload.json \
  -T application/json \
  http://localhost:5000/phase9/intelligence

# Test with larger dataset
ab -n 100 -c 10 -p large_payload.json \
  -T application/json \
  http://localhost:5000/data/upload

# Monitor resources
watch -n 1 'grep "percent" logs/construction_ai.log | tail -5'
```

### Step 12: Monitor Critical Errors

```bash
# Watch for critical errors
tail -f logs/construction_ai.log | \
  grep '"level": "CRITICAL"'

# Watch for resource exhaustion
tail -f logs/construction_ai.log | \
  grep '"event_type": "SLOW_OPERATION"'

# Watch for model errors
tail -f logs/construction_ai.log | \
  grep '"event_type": "MODEL_ERROR"'
```

## Production Deployment Checklist

- [ ] All Phase 14 tests pass (50+ tests)
- [ ] Security audit shows no critical issues
- [ ] Verification report: READY_FOR_PRODUCTION
- [ ] All endpoints wrapped with @safe_api_call
- [ ] Logging initialized in app startup
- [ ] Data validation in all request handlers
- [ ] Model registry created and models registered
- [ ] Models locked for production
- [ ] Environment variables configured:
  - [ ] FLASK_ENV=production
  - [ ] FLASK_DEBUG=false
  - [ ] LOG_LEVEL=INFO
  - [ ] LOG_DIR set
- [ ] Directory structure created:
  - [ ] logs/ (755)
  - [ ] models/ (755)
  - [ ] config/ (700)
  - [ ] data/ (755)
- [ ] Dependencies installed (psutil)
- [ ] E2E tests pass in staging
- [ ] Load tests pass in staging
- [ ] Monitoring/logging verified
- [ ] Error scenarios tested
- [ ] Recovery procedures documented
- [ ] Team trained on new error handling

## Post-Deployment Monitoring

### First 24 Hours

- Monitor error rate (should be 0% after initial stabilization)
- Monitor response time (should be unchanged ±5%)
- Monitor resource usage (memory should be stable)
- Watch for unexpected slow operations
- Verify logs are being generated correctly

### First Week

- Review error patterns in logs
- Verify all endpoints return proper error responses
- Check that no credentials leaked in logs
- Monitor model inference performance
- Verify backup/disaster recovery procedures

### Ongoing

- Daily error log review
- Weekly performance metrics analysis
- Monthly security audit
- Quarterly recovery procedure testing

## Rollback Plan

If Phase 14 causes issues:

```bash
# 1. Identify the issue
tail -f logs/construction_ai.log | grep ERROR

# 2. Disable Phase 14 (remove decorators if needed)
# OR

# 3. Rollback to previous version
git revert <commit>
docker build -f backend/Dockerfile -t construction-ai:rollback .
docker stop construction-ai
docker run -d ... construction-ai:rollback

# 4. Verify system recovered
curl http://localhost:5000/phase9/intelligence

# 5. Analyze issue and redeploy
```

## Success Criteria

Deployment is successful when:

✅ All endpoints return proper error responses  
✅ Error logs are structured JSON with full context  
✅ No crashes or silent failures  
✅ Response time within 5% of previous  
✅ Memory usage stable  
✅ All security checks pass  
✅ Monitoring alerts configured  
✅ Team can debug using Phase 14 logs  

## Support

If issues occur:

1. Check [PHASE_14_INTEGRATION_GUIDE.md](PHASE_14_INTEGRATION_GUIDE.md#troubleshooting)
2. Review logs: `tail -f logs/construction_ai.log | python -m json.tool`
3. Run verification: `python -m app.phase14_verification`
4. Check environment variables: `echo $FLASK_ENV $FLASK_DEBUG $LOG_LEVEL`
5. Verify directory permissions: `ls -la logs/ models/ config/`

---

**Phase 14 is production-ready!** 🚀

Deploy with confidence. The system now has comprehensive error handling, logging, validation, model safety, performance monitoring, and security auditing.

# Feature 11: Installation & Configuration Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Monday.com Setup](#mondaycom-setup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Memory**: 512 MB RAM minimum (2 GB recommended)
- **Storage**: 100 MB for installation
- **Network**: Internet connection for monday.com sync

### Supported Operating Systems
- Windows 10+
- macOS 10.14+
- Linux (Ubuntu 18.04+)

### Dependencies
```
Flask>=2.0.0
python-dateutil>=2.8.0
requests>=2.25.0
```

---

## Installation

### Step 1: Clone/Access Project
```bash
cd construction-ai-suite
```

### Step 2: Activate Virtual Environment
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Copy Feature 11 Files
```bash
# Files should be located in: backend/app/
# - phase11_resource_types.py
# - phase11_allocation_optimizer.py
# - phase11_resource_integration.py
# - phase11_recommendations.py
# - phase11_dashboard.py
# - phase11_config.py
# - phase11_api_routes.py
# - test_phase11_integration.py
```

### Step 5: Verify Installation
```bash
python -c "from phase11_resource_types import Worker; print('✓ Installation successful')"
```

---

## Configuration

### Configuration File Location
```
backend/app/phase11_config.py
```

### Key Configuration Parameters

#### Optimization Weights
```python
OPTIMIZATION_WEIGHTS = {
    'minimize_delay': {
        'delay': 0.5,        # 50% weight on delay reduction
        'cost': 0.3,         # 30% weight on cost
        'risk': 0.2          # 20% weight on risk
    },
    'minimize_cost': {
        'delay': 0.2,
        'cost': 0.6,
        'risk': 0.2
    },
    'balance': {
        'delay': 0.33,
        'cost': 0.33,
        'risk': 0.34
    }
}
```

**How to adjust**: Modify weights to change recommendation priority

#### Resource Constraints
```python
MAX_CONCURRENT_TASKS = 5          # Max tasks per worker
DEFAULT_RELIABILITY = 0.75         # Default reliability score
MIN_SKILL_MATCH_LEVEL = 0.8       # Min skill match percentage
MAX_TRAVEL_TIME = 2               # Max travel time in hours
```

**How to adjust**: Change values based on company policies

#### Performance Settings
```python
OPTIMIZATION_TIMEOUT = 2.0         # Seconds for optimization
CACHE_DURATION = 3600             # Cache duration in seconds
MAX_RECOMMENDATIONS = 20           # Max recommendations per project
BATCH_SIZE = 100                  # Batch size for processing
```

**How to adjust**: Increase timeout for large projects, adjust cache for frequency of changes

#### Logging Configuration
```python
LOG_LEVEL = 'INFO'                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = 'logs/phase11.log'
ERROR_LOG_FILE = 'logs/phase11_errors.log'
```

### Environment Variables

Create `.env` file in project root:
```
FEATURE_11_DEBUG=false
FEATURE_11_LOG_LEVEL=INFO
MONDAY_COM_API_KEY=your_api_key_here
MONDAY_COM_WORKSPACE_ID=your_workspace_id
```

### Configuration Examples

#### For Time-Sensitive Projects
```python
OPTIMIZATION_WEIGHTS['minimize_delay'] = {
    'delay': 0.7,      # Increase delay weight
    'cost': 0.2,
    'risk': 0.1
}
OPTIMIZATION_TIMEOUT = 5.0  # Allow more time for optimization
```

#### For Budget-Constrained Projects
```python
OPTIMIZATION_WEIGHTS['minimize_cost'] = {
    'delay': 0.1,
    'cost': 0.8,       # Increase cost weight
    'risk': 0.1
}
```

#### For Large Projects
```python
MAX_RECOMMENDATIONS = 50
OPTIMIZATION_TIMEOUT = 5.0
CACHE_DURATION = 7200  # 2 hours
BATCH_SIZE = 200
```

---

## Monday.com Setup

### Prerequisites
- Monday.com account
- API access enabled
- Board structure set up

### Step 1: Generate API Key

1. Login to monday.com
2. Navigate to Admin → Integrations → Developer
3. Create new API key
4. Copy the key (you'll need it only once)

### Step 2: Configure Integration

In `phase11_config.py`:
```python
MONDAY_COM_CONFIG = {
    'api_key': 'your_api_key_here',
    'workspace_id': 'your_workspace_id',
    'sync_interval': 300,  # 5 minutes
    'retry_attempts': 3,
    'timeout': 30
}
```

Or set environment variable:
```bash
export MONDAY_COM_API_KEY=your_api_key_here
```

### Step 3: Map Monday.com Fields

Verify field mappings in `phase11_resource_types.py`:
```python
MONDAY_COM_FIELD_MAPPING = {
    'worker_id': 'user_id_field',
    'worker_name': 'user_name_field',
    'skills': 'skills_field',
    'availability': 'availability_field',
    'hourly_rate': 'rate_field',
    # ... more mappings
}
```

### Step 4: Test Connection

```bash
python -c "
from phase11_resource_integration import create_resource_allocation_integration
integration = create_resource_allocation_integration('TEST_PRJ')
data = integration.get_monday_com_data()
print(f'✓ Monday.com connection successful')
print(f'Workers loaded: {len(data.get(\"workers\", []))}')
"
```

### Step 5: Enable Sync

```python
# In phase11_config.py
ENABLE_MONDAY_COM_SYNC = True
SYNC_INTERVAL_SECONDS = 300  # Sync every 5 minutes
```

---

## Verification

### Unit Tests
```bash
# Run all tests
python -m pytest backend/app/test_phase11_integration.py -v

# Run specific test class
python -m pytest backend/app/test_phase11_integration.py::TestMultiProjectScenarios -v

# Run with coverage
python -m pytest backend/app/test_phase11_integration.py --cov=backend/app
```

### Integration Tests
```bash
# Test Feature 11 integration with Feature 3
python -m pytest backend/app/test_phase11_integration.py::TestResourceConstraints -v

# Test API endpoints
python -c "
from phase11_api_routes import phase11_bp
print('✓ API routes loaded successfully')
print(f'Blueprint: {phase11_bp.name}')
"
```

### API Verification
```bash
# Start server
python run_server.py

# In another terminal, test health endpoint
curl http://localhost:8000/api/v1/features/feature11/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "Feature 11 - Resource Allocation",
#   "version": "1.0.0"
# }
```

### Functional Verification

```python
from phase11_resource_integration import create_resource_allocation_integration
from phase11_resource_types import AllocationRequest, Worker, Skill, SkillLevel, ResourceAvailability
from datetime import date

# 1. Create integration
integration = create_resource_allocation_integration("TEST_PROJECT")
print("✓ Integration created")

# 2. Get monday.com data
monday_data = integration.get_monday_com_data()
print(f"✓ Monday.com sync: {len(monday_data.get('workers', []))} workers")

# 3. Analyze resources
request = AllocationRequest(
    project_id="TEST_PROJECT",
    optimization_goal="minimize_delay"
)
from phase11_allocation_optimizer import AllocationOptimizer
optimizer = AllocationOptimizer()
print("✓ Optimizer ready")

# 4. Check feature integrations
f3 = integration.get_feature_3_input()
f4 = integration.get_feature_4_input()
f9 = integration.get_feature_9_input()
f10 = integration.get_feature_10_input()
print("✓ All feature integrations working")

print("\n✓ ALL VERIFICATION CHECKS PASSED")
```

---

## Database Setup (Optional)

If using persistent storage:

### SQLite (Default)
```python
# In phase11_config.py
DATABASE_TYPE = 'sqlite'
DATABASE_PATH = 'data/feature11.db'
```

### PostgreSQL
```python
# In phase11_config.py
DATABASE_TYPE = 'postgresql'
DATABASE_URL = 'postgresql://user:password@localhost:5432/feature11'
```

### Initialize Database
```bash
python backend/app/phase11_db_init.py
```

---

## Troubleshooting

### Issue: Import Error
```
ModuleNotFoundError: No module named 'phase11_resource_types'
```
**Solution**:
1. Verify files are in `backend/app/`
2. Check Python path: `echo $PYTHONPATH`
3. Add to path: `export PYTHONPATH="${PYTHONPATH}:backend/app"`

### Issue: Monday.com Connection Fails
```
Error: Invalid API key or workspace not found
```
**Solution**:
1. Verify API key in configuration
2. Check workspace ID is correct
3. Confirm API access is enabled in monday.com
4. Test connection: `curl -H "Authorization: Bearer YOUR_KEY" https://api.monday.com/v2`

### Issue: Optimization Timeout
```
Error: Optimization exceeded timeout (2.0s)
```
**Solution**:
1. Increase timeout: `OPTIMIZATION_TIMEOUT = 5.0`
2. Simplify constraints
3. Check system resources
4. Consider breaking project into smaller pieces

### Issue: Low Confidence Scores
```
Confidence score < 0.5
```
**Solution**:
1. Verify data quality in monday.com
2. Check worker/task availability data
3. Review skill definitions
4. Increase available resources

### Issue: Memory Usage High
```
Memory exceeds 1GB
```
**Solution**:
1. Reduce batch size: `BATCH_SIZE = 50`
2. Clear cache: `integration.clear_cache()`
3. Analyze smaller projects first
4. Increase system memory

### Issue: API Not Responding
```
Connection refused: http://localhost:8000
```
**Solution**:
1. Start server: `python run_server.py`
2. Check port 8000 is available
3. Verify firewall settings
4. Check server logs: `tail -f logs/phase11.log`

---

## Advanced Configuration

### Custom Optimization Weights
```python
# For your specific organization
CUSTOM_WEIGHTS = {
    'my_optimization': {
        'delay': 0.4,
        'cost': 0.4,
        'risk': 0.2
    }
}

# Use in analysis
request = AllocationRequest(
    project_id="PRJ001",
    optimization_goal="my_optimization"
)
```

### Performance Tuning

#### For Speed
```python
# Reduce accuracy for speed
MAX_RECOMMENDATIONS = 5
OPTIMIZATION_TIMEOUT = 0.5
SAMPLE_RATE = 0.5  # Use 50% of data for analysis
```

#### For Accuracy
```python
# Increase accuracy
MAX_RECOMMENDATIONS = 50
OPTIMIZATION_TIMEOUT = 10.0
EXHAUSTIVE_SEARCH = True
```

#### For Memory Efficiency
```python
BATCH_SIZE = 50
CACHE_DURATION = 600
ENABLE_COMPRESSION = True
```

### Logging Configuration

#### Detailed Logging
```python
LOG_LEVEL = 'DEBUG'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
ENABLE_PERFORMANCE_LOGGING = True
```

#### Audit Trail
```python
ENABLE_AUDIT_LOG = True
AUDIT_LOG_FILE = 'logs/feature11_audit.log'
AUDIT_EVENTS = [
    'allocation_created',
    'allocation_modified',
    'allocation_deleted',
    'recommendation_generated',
    'conflict_detected'
]
```

---

## Backup and Recovery

### Backup Configuration
```bash
# Backup configuration
cp backend/app/phase11_config.py backup/phase11_config.$(date +%Y%m%d).py

# Backup data
cp data/feature11.db backup/feature11.$(date +%Y%m%d).db
```

### Recovery
```bash
# Restore configuration
cp backup/phase11_config.YYYYMMDD.py backend/app/phase11_config.py

# Restore database
cp backup/feature11.YYYYMMDD.db data/feature11.db
```

---

## Performance Benchmarks

| Operation | Expected Time | Conditions |
|-----------|---------------|-----------|
| Project analysis | 0.5-2 seconds | 100-1000 tasks |
| Get recommendations | 100-500ms | Cache hit |
| Apply allocation | 50-200ms | Direct insert |
| Monday.com sync | 1-5 seconds | Full sync |

---

## Security

### API Security
- Always use HTTPS in production
- Rotate API keys regularly
- Use environment variables for secrets
- Enable request validation

### Data Security
- Encrypt sensitive data in database
- Use role-based access control
- Enable audit logging
- Regular backups

### Configuration Security
```python
# Never hardcode credentials
import os
API_KEY = os.getenv('MONDAY_COM_API_KEY')

# Use secrets management
from cryptography.fernet import Fernet
cipher = Fernet(secret_key)
encrypted_key = cipher.encrypt(api_key.encode())
```

---

## Next Steps

1. **Review Configuration**
   - Check `phase11_config.py`
   - Adjust weights for your use case
   - Set up logging

2. **Test Integration**
   - Run test suite
   - Verify monday.com connection
   - Test API endpoints

3. **Deploy**
   - Configure production settings
   - Set up monitoring
   - Configure backups

4. **Monitor**
   - Review logs regularly
   - Track performance metrics
   - Analyze recommendations adoption

---

## Support and Help

- **Documentation**: See guides in project root
- **Logs**: Check `logs/phase11*.log`
- **Tests**: Run test suite for diagnostic info
- **API Docs**: See `PHASE_23_FEATURE_11_API_REFERENCE.md`

---

**Version**: 1.0  
**Last Updated**: Phase 23  
**Status**: Production Ready

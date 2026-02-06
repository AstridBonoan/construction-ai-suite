# Feature 11: Troubleshooting & FAQ

## Table of Contents
1. [Common Issues](#common-issues)
2. [API Issues](#api-issues)
3. [Monday.com Integration Issues](#mondaycom-integration-issues)
4. [Performance Issues](#performance-issues)
5. [Data Issues](#data-issues)
6. [Frequently Asked Questions](#frequently-asked-questions)
7. [Getting Help](#getting-help)

---

## Common Issues

### Issue 1: ImportError When Starting Service

**Error Message:**
```
ModuleNotFoundError: No module named 'phase11_resource_types'
```

**Root Causes:**
- Feature 11 files not in `backend/app/`
- Python path not set correctly
- Virtual environment not activated

**Solution:**
```bash
# 1. Verify files exist
ls -la backend/app/phase11*.py

# 2. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
or
.venv\Scripts\activate  # Windows

# 3. Verify Python path
export PYTHONPATH="${PYTHONPATH}:backend/app"

# 4. Test import
python -c "from phase11_resource_types import Worker; print('Success')"
```

---

### Issue 2: Service Won't Start

**Error Message:**
```
Address already in use: ('127.0.0.1', 8000)
```

**Root Causes:**
- Port 8000 already in use
- Service already running
- Orphaned process

**Solution:**
```bash
# 1. Find process on port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 2. Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# 3. Restart service
python run_server.py
```

---

### Issue 3: High Memory Usage

**Symptom:**
```
Memory usage exceeds 1GB, process slows down
```

**Root Causes:**
- Large project analysis
- Insufficient garbage collection
- Memory leak in cache

**Investigation:**
```bash
# Check memory usage
ps aux | grep python

# Monitor in real-time
watch -n 1 'ps aux | grep python'
```

**Solution:**
```python
# 1. Clear cache periodically
integration.clear_cache()

# 2. Reduce batch size
BATCH_SIZE = 50  # In phase11_config.py

# 3. Break large projects
# Analyze by phase instead of entire project

# 4. Increase system memory
# Add more RAM if available

# 5. Monitor memory
import tracemalloc
tracemalloc.start()
# ... your code ...
current, peak = tracemalloc.get_traced_memory()
print(f"Peak: {peak / 1024 / 1024:.1f} MB")
```

---

### Issue 4: Slow Optimization

**Symptom:**
```
Optimization taking > 10 seconds
```

**Root Causes:**
- Large project (1000+ tasks)
- Complex constraints
- System under load

**Investigation:**
```bash
# Check logs
tail -20 logs/phase11_performance.log | grep "Optimization completed"

# Count tasks
curl http://localhost:8000/api/v1/features/feature11/projects/PRJ001/tasks | jq '.total_tasks'

# Check system load
top -bn1 | head -10
```

**Solution:**
```python
# 1. Increase timeout
OPTIMIZATION_TIMEOUT = 5.0  # Increased from 2.0

# 2. Reduce recommendations
MAX_RECOMMENDATIONS = 10  # Reduced from 20

# 3. Use sampling
SAMPLE_RATE = 0.5  # Use 50% of data

# 4. Break into phases
# PRJ001_Phase1, PRJ001_Phase2, etc.

# 5. Simplify constraints
# Disable non-critical constraints
```

---

### Issue 5: Low Confidence Scores

**Symptom:**
```
Confidence score < 0.5
Recommendations have low reliability
```

**Root Causes:**
- Incomplete data
- Conflicting constraints
- Insufficient resources

**Investigation:**
```python
# Check data quality
integration = create_resource_allocation_integration("PRJ001")
workers = integration.get_monday_com_data()['workers']
tasks = integration.get_feature_4_input()['tasks']

print(f"Workers with skills: {sum(1 for w in workers if w.get('skills'))}")
print(f"Tasks with requirements: {sum(1 for t in tasks if t.get('required_skills'))}")

# Check for conflicts
conflicts = integration.get_resource_conflicts()
print(f"Conflicts: {len(conflicts)}")
```

**Solution:**
```python
# 1. Improve data quality
# Ensure all workers have skills defined
# Ensure all tasks have requirements

# 2. Resolve conflicts first
# Address overallocations
# Fill skill gaps

# 3. Add more resources
# Bring in subcontractors
# Extend timeline

# 4. Simplify optimization
# Use "balance" goal
# Reduce constraints
```

---

## API Issues

### Issue 6: 400 Bad Request

**Error Message:**
```json
{
  "success": false,
  "error": "Invalid project_id format"
}
```

**Root Causes:**
- Missing required fields
- Invalid data format
- Invalid field values

**Solution:**
```bash
# Check request format
curl -X POST http://localhost:8000/api/v1/features/feature11/projects/PRJ001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "optimization_goal": "minimize_delay",
    "max_recommendations": 10
  }'

# Verify project_id exists
curl http://localhost:8000/api/v1/features/feature11/projects/PRJ001/health

# Check parameter values
# Valid optimization_goals: "minimize_delay", "minimize_cost", "balance"
# Valid max_recommendations: 1-100
```

---

### Issue 7: 404 Not Found

**Error Message:**
```json
{
  "success": false,
  "error": "Project PRJ001 not found"
}
```

**Root Causes:**
- Project doesn't exist
- Project ID typo
- Wrong endpoint

**Solution:**
```bash
# Verify project exists in monday.com
curl http://localhost:8000/api/v1/features/feature11/projects/PRJ001/resources

# Check project ID spelling
# Case-sensitive!
echo "PRJ001" vs "prj001"

# Verify endpoint URL
# Should be: /api/v1/features/feature11/projects/{id}/...
```

---

### Issue 8: 500 Internal Server Error

**Error Message:**
```json
{
  "success": false,
  "error": "Error analyzing resources: [details]"
}
```

**Root Causes:**
- Code bug
- Database connection error
- Monday.com API failure
- Out of memory

**Solution:**
```bash
# 1. Check error logs
tail -50 logs/phase11_errors.log

# 2. Check system resources
free -h
df -h

# 3. Restart service
systemctl restart feature11

# 4. Check database connectivity
sqlite3 data/feature11.db ".tables"

# 5. Test Monday.com connection
curl -H "Authorization: Bearer $API_KEY" https://api.monday.com/v2

# 6. Report to support with:
#    - Request details
#    - Timestamp
#    - Error logs
#    - Project size (task count)
```

---

### Issue 9: API Timeout

**Symptom:**
```
Connection timeout after 30 seconds
Request still processing
```

**Solution:**
```bash
# 1. Increase timeout in client
# Python requests default: 30 seconds
requests.post(url, json=data, timeout=60)

# 2. Check server logs
tail -f logs/phase11_performance.log

# 3. Increase server timeout
# In nginx: proxy_read_timeout 120s
# In Flask: PROPAGATE_EXCEPTIONS = True

# 4. For large projects:
# Break into smaller projects
# Or run as background job
```

---

### Issue 10: Rate Limiting

**Error Message:**
```json
{
  "success": false,
  "error": "Rate limit exceeded: 1000 requests/minute"
}
```

**Solution:**
```python
# Check rate limit headers
response = requests.get(url)
print(response.headers.get('X-RateLimit-Remaining'))

# 1. Reduce request frequency
import time
for project_id in projects:
    analyze(project_id)
    time.sleep(1)  # 1 second between requests

# 2. Use batch API
# Analyze multiple projects in single call

# 3. Request rate limit increase
# Contact support@company.com
```

---

## Monday.com Integration Issues

### Issue 11: Monday.com Connection Failed

**Error Message:**
```
Error: Connection to monday.com API failed
```

**Root Causes:**
- Invalid API key
- Network connectivity
- Monday.com API down

**Investigation:**
```bash
# Test network connectivity
ping api.monday.com

# Test Monday.com API
curl -X POST https://api.monday.com/v2 \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "query": "{ boards { id name } }"
  }'

# Check API key validity
echo $MONDAY_COM_API_KEY
```

**Solution:**
```python
# 1. Verify API key in configuration
from phase11_config import MONDAY_COM_CONFIG
print(MONDAY_COM_CONFIG['api_key'][:10] + "...")

# 2. Generate new API key if expired
# Login to monday.com → Admin → Integrations → Developer

# 3. Set environment variable
export MONDAY_COM_API_KEY="your_new_key"

# 4. Restart service
systemctl restart feature11

# 5. Test connection
integration = create_resource_allocation_integration("TEST")
data = integration.get_monday_com_data()
print("Connection successful")
```

---

### Issue 12: Worker Data Not Syncing

**Symptom:**
```
Workers exist in monday.com but not in Feature 11
```

**Root Causes:**
- Sync not enabled
- User doesn't have monday.com access
- Field mapping incorrect

**Solution:**
```python
# 1. Enable sync
ENABLE_MONDAY_COM_SYNC = True  # In phase11_config.py

# 2. Verify field mapping
from phase11_resource_types import MONDAY_COM_FIELD_MAPPING
print(MONDAY_COM_FIELD_MAPPING)

# 3. Check user permissions
# Verify API key has user.me scope

# 4. Manual sync
integration = create_resource_allocation_integration("PRJ001")
integration.sync_monday_com(force=True)

# 5. Check sync logs
grep "Monday.com" logs/phase11.log
```

---

### Issue 13: Monday.com Sync Slow

**Symptom:**
```
Sync takes > 30 seconds
```

**Solution:**
```python
# 1. Reduce sync frequency
SYNC_INTERVAL_SECONDS = 600  # Instead of 300

# 2. Sync only changed projects
integration.sync_monday_com(incremental=True)

# 3. Check Monday.com API limits
# 100 requests per minute per API key
# Optimize query to fetch less data

# 4. Check network
# Use faster network connection

# 5. Profile sync
import cProfile
cProfile.run('integration.sync_monday_com()')
```

---

## Performance Issues

### Issue 14: Cache Not Working

**Symptom:**
```
Cache hit rate < 50%
Same queries take same time repeatedly
```

**Investigation:**
```python
# Check cache stats
cache_stats = integration.get_cache_stats()
print(f"Hit rate: {cache_stats['hit_rate']:.0%}")
print(f"Cache size: {cache_stats['size']}")

# Check cache duration
from phase11_config import CACHE_DURATION
print(f"Cache duration: {CACHE_DURATION} seconds")
```

**Solution:**
```python
# 1. Increase cache duration
CACHE_DURATION = 7200  # 2 hours instead of 1

# 2. Verify cache is enabled
ENABLE_CACHING = True

# 3. Check cache implementation
integration.clear_cache()
integration.enable_cache()

# 4. Monitor cache effectiveness
# If hit rate < 60%, consider reducing duration
```

---

### Issue 15: Recommendation Quality Poor

**Symptom:**
```
Recommendations not helpful
Same recommendations every time
```

**Solution:**
```python
# 1. Verify data freshness
# Last Monday.com sync:
grep "Sync completed" logs/phase11.log | tail -1

# 2. Generate with different goal
request = AllocationRequest(
    project_id="PRJ001",
    optimization_goal="minimize_cost"  # Try different
)

# 3. Review confidence scores
result = analyze_project_resources(integration, request)
print(f"Confidence: {result.confidence_score}")

# 4. Increase recommendation count
request.max_recommendations = 50  # From 10

# 5. Review constraints
# May be too restrictive
```

---

## Data Issues

### Issue 16: Data Corruption in Database

**Symptom:**
```
Error: database disk image is malicious
or
Error: SQLite database corrupted
```

**Solution:**
```bash
# 1. Check database integrity
sqlite3 data/feature11.db "PRAGMA integrity_check;"

# 2. Repair database
sqlite3 data/feature11.db
> .dump > backup.sql
> .restore backup.sql

# 3. Restore from backup
cp backup/feature11_YYYYMMDD.db data/feature11.db

# 4. Rebuild database
rm data/feature11.db
python backend/app/phase11_db_init.py
```

---

### Issue 17: Duplicate Allocations

**Symptom:**
```
Same task allocated to same worker twice
```

**Root Causes:**
- Double-click on apply
- Race condition
- Sync issue

**Solution:**
```python
# 1. Check for duplicates
duplicates = integration.find_duplicate_allocations()

# 2. Remove duplicates
integration.remove_duplicate_allocations()

# 3. Verify with query
import sqlite3
conn = sqlite3.connect('data/feature11.db')
cursor = conn.cursor()
cursor.execute("""
  SELECT task_id, worker_id, COUNT(*) 
  FROM allocations 
  GROUP BY task_id, worker_id 
  HAVING COUNT(*) > 1
""")
duplicates = cursor.fetchall()
```

---

## Frequently Asked Questions

### Q1: How often should I analyze resources?

**A:** 
- New projects: Daily
- Active projects: 2-3 times per week
- Stable projects: Weekly
- Or after significant changes (worker availability, new tasks, delays)

---

### Q2: Can I use Feature 11 with multiple projects simultaneously?

**A:**
Yes! Each project is independent. You can analyze multiple projects in parallel:
```python
from concurrent.futures import ThreadPoolExecutor

projects = ["PRJ001", "PRJ002", "PRJ003"]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(analyze_project, projects)
```

---

### Q3: What's the maximum project size?

**A:**
- Small: < 100 tasks (< 1 second optimization)
- Medium: 100-500 tasks (1-3 seconds)
- Large: 500-1000 tasks (3-5 seconds)
- Very Large: > 1000 tasks (break into phases)

---

### Q4: Can I modify recommendations before applying?

**A:**
Not directly through API, but you can:
1. Get recommendations
2. Implement manually with partial recommendations
3. Or use different optimization goal for different results

---

### Q5: How do I integrate with my project management tool?

**A:**
Options:
1. **Monday.com**: Already integrated
2. **Other tools**: Use REST API to fetch data and apply allocations
3. **webhooks**: Configure to sync on changes

```python
# Example: Fetch from external API
response = requests.get("https://api.otherpm.com/tasks")
tasks = response.json()
# Map to Feature 11 TaskResourceRequirement
# Analyze and get recommendations
```

---

### Q6: What if a recommendation is wrong?

**A:**
1. Don't apply it
2. Generate different recommendations with different goal
3. Check data quality (worker skills, task requirements)
4. Manually apply alternative allocation

---

### Q7: How do I train team on Feature 11?

**A:**
Resources:
- Quick Reference: `PHASE_23_FEATURE_11_QUICK_REFERENCE.md`
- Developer Guide: `PHASE_23_FEATURE_11_DEVELOPER_GUIDE.py`
- API Reference: `PHASE_23_FEATURE_11_API_REFERENCE.md`
- Setup Guide: `PHASE_23_FEATURE_11_SETUP_GUIDE.md`

---

### Q8: Is my data secure?

**A:**
Security measures:
- API key authentication
- Request validation
- Audit logging
- Database encryption (optional)
- Rate limiting
- Access control

---

### Q9: Can I export data?

**A:**
Yes, multiple formats:
```python
# CSV export
export_allocations("PRJ001", format='csv')

# JSON export
export_allocations("PRJ001", format='json')

# Custom export
def custom_export(project_id):
    allocations = integration.get_current_allocations()
    # Your export logic
```

---

### Q10: What happens if monday.com is down?

**A:**
Feature 11 will:
1. Use cached data from last sync
2. Retry sync with backoff
3. Alert if sync fails repeatedly
4. Continue to work with stale data

```python
# Check last sync
last_sync = integration.get_last_sync_time()
time_since_sync = datetime.now() - last_sync

if time_since_sync > timedelta(hours=1):
    logging.warning("Data may be stale, Monday.com not synced for 1 hour")
```

---

## Getting Help

### Support Channels

1. **Documentation**
   - Guides in project root
   - Code comments in files
   - Test examples

2. **Developer Resources**
   - `PHASE_23_FEATURE_11_DEVELOPER_GUIDE.py` - 15 sections with examples
   - `PHASE_23_FEATURE_11_API_REFERENCE.md` - Full API docs
   - `test_phase11_integration.py` - Test examples

3. **Community**
   - Github Issues
   - Slack channel
   - Mailing list

4. **Premium Support**
   - Email: support@company.com
   - Phone: 555-1234
   - Response time: 1 hour

### When Contacting Support

Include:
```
1. Error message or symptom
2. Project ID and size (task count)
3. Recent logs (last 100 lines)
4. Steps to reproduce
5. System info (OS, Python version)
6. Monday.com workspace info (if relevant)

Example:
Support request:
- Issue: High memory usage when analyzing PRJ001
- Project size: 1200 tasks
- Symptom: Process uses 1.5GB, slows down after 5 minutes
- Logs: [attached]
- System: Ubuntu 20.04, Python 3.9
```

---

**Version**: 1.0  
**Last Updated**: Phase 23  
**Status**: Production Ready

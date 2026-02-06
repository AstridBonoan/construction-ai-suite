# Feature 11: Administrator & Operations Guide

## Table of Contents
1. [System Monitoring](#system-monitoring)
2. [Performance Management](#performance-management)
3. [Maintenance Tasks](#maintenance-tasks)
4. [User Management](#user-management)
5. [Data Management](#data-management)
6. [Incident Response](#incident-response)
7. [Reporting](#reporting)

---

## System Monitoring

### Key Metrics to Monitor

#### Real-time Dashboard Metrics
```python
integration.get_allocation_metrics()

Returns:
{
    'total_workers': 15,
    'average_utilization': 0.82,        # Should be > 0.70
    'unallocated_hours': 120,           # Should be < 20% of total
    'conflict_count': 3,                # Monitor trend
    'compliance_status': 'on_track',    # on_track, at_risk, critical
    'estimated_delay_risk': 0.25,       # Should be < 0.30
    'critical_skills_gap': ['electrical:senior']
}
```

#### Performance Metrics
```
API Response Time:      Track in logs/phase11_performance.log
Optimization Time:      Monitor for > 5 seconds
Cache Hit Rate:         Should be > 0.8 (80%)
Error Rate:             Should be < 0.01 (1%)
Monday.com Sync Time:   Should be < 5 seconds
```

#### Health Indicators
| Indicator | Threshold | Action |
|-----------|-----------|--------|
| Utilization | < 0.50 | Underutilized - review allocations |
| Utilization | > 0.95 | Over-utilized - consider resources |
| Unallocated Hours | > 30% | Significant gap - add resources |
| Conflict Count | > 10 | Address conflicts |
| Delay Risk | > 0.40 | High risk - escalate |
| Error Rate | > 0.02 | Investigate errors |

### Monitoring Setup

#### Log File Locations
```
logs/phase11.log                    # Main operations log
logs/phase11_performance.log        # Performance metrics
logs/phase11_errors.log             # Error log
logs/phase11_audit.log              # Audit trail
```

#### Enable Performance Monitoring
```python
# In phase11_config.py
ENABLE_PERFORMANCE_LOGGING = True
PERFORMANCE_LOG_FILE = 'logs/phase11_performance.log'
LOG_LEVEL = 'INFO'
```

#### Create Monitoring Script
```python
import logging
from datetime import datetime
import json

def monitor_system_health():
    """Monitor system health and alert on issues"""
    integration = create_resource_allocation_integration("MONITOR")
    
    metrics = integration.get_allocation_metrics()
    
    issues = []
    
    if metrics['average_utilization'] < 0.50:
        issues.append("WARN: Low utilization")
    
    if metrics['conflict_count'] > 10:
        issues.append("ALERT: High conflict count")
    
    if metrics['estimated_delay_risk'] > 0.40:
        issues.append("CRITICAL: High delay risk")
    
    # Log and alert
    for issue in issues:
        logging.warning(issue)
    
    return metrics, issues

# Run periodically (every 5 minutes)
```

---

## Performance Management

### Optimization Performance

#### Monitoring Optimization Speed
```bash
# Check logs for optimization times
grep "Optimization completed in" logs/phase11_performance.log

# Expected: < 2 seconds for typical projects
# Alert if: > 5 seconds
```

#### Improving Performance

**If optimization is slow:**

1. **Check project size**
   ```bash
   # Count tasks in project
   curl http://localhost:8000/api/v1/features/feature11/projects/PRJ001/tasks | jq '.total_tasks'
   ```

2. **Increase timeout**
   ```python
   # In phase11_config.py
   OPTIMIZATION_TIMEOUT = 5.0  # Increased from 2.0
   ```

3. **Reduce recommendations**
   ```python
   MAX_RECOMMENDATIONS = 10  # Reduced from 20
   ```

4. **Break into sub-projects**
   ```python
   # For projects with 1000+ tasks, split into phases
   # E.g., "PRJ001_Phase1", "PRJ001_Phase2"
   ```

### Cache Management

#### Monitor Cache Efficiency
```python
# Check cache hit rate
cache_stats = integration.get_cache_stats()

print(f"Cache hits: {cache_stats['hits']}")        # Should be high
print(f"Cache misses: {cache_stats['misses']}")    # Should be low
print(f"Hit rate: {cache_stats['hit_rate']:.0%}")  # Should be > 80%
```

#### Clear Cache When Needed
```python
# Manual cache clear
integration.clear_cache()
logging.info("Cache cleared")

# Or by time
integration.clear_old_cache(max_age_seconds=3600)
```

#### Cache Configuration
```python
# In phase11_config.py
CACHE_DURATION = 3600              # 1 hour
CACHE_MAX_SIZE = 100               # Max items
ENABLE_CACHE_COMPRESSION = True
CACHE_CLEANUP_INTERVAL = 300       # 5 minutes
```

### Resource Management

#### Monitor Memory Usage
```bash
# Linux/Mac
ps aux | grep python | grep run_server

# Shows: %mem (should be < 20% of system RAM)
```

#### Monitor Database Size
```bash
# Check database size
du -sh data/feature11.db

# If growing too large, archive old data
sqlite3 data/feature11.db "SELECT COUNT(*) FROM allocations WHERE created_date < date('now', '-90 days')"
```

---

## Maintenance Tasks

### Daily Tasks

#### Check Error Logs
```bash
# Review errors from previous 24 hours
tail -100 logs/phase11_errors.log

# Alert if error rate > 1%
grep -c ERROR logs/phase11_errors.log | awk '{print $1 / NR}'
```

#### Verify Monday.com Sync
```bash
# Check last successful sync
grep "Monday.com sync completed" logs/phase11.log | tail -1

# If no sync in 30 minutes, investigate
```

#### Monitor System Resources
```bash
# Check disk space
df -h | grep -E "^/dev/|Filesystem"

# Alert if > 90% full
```

### Weekly Tasks

#### Performance Review
```python
def weekly_performance_report():
    """Generate weekly performance report"""
    
    # Get weekly metrics
    start_date = datetime.now() - timedelta(days=7)
    
    # 1. Analyze logs
    with open('logs/phase11_performance.log') as f:
        lines = f.readlines()
    
    avg_response_time = calculate_avg_response_time(lines)
    avg_optimization_time = calculate_avg_optimization_time(lines)
    
    # 2. Check error rate
    with open('logs/phase11_errors.log') as f:
        error_count = len(f.readlines())
    
    total_operations = get_total_operations(start_date)
    error_rate = error_count / total_operations if total_operations > 0 else 0
    
    # 3. Generate report
    print(f"WEEKLY PERFORMANCE REPORT")
    print(f"========================")
    print(f"Avg Response Time: {avg_response_time:.2f}ms")
    print(f"Avg Optimization Time: {avg_optimization_time:.2f}s")
    print(f"Error Rate: {error_rate:.2%}")
    print(f"Total Operations: {total_operations}")
    
    return {
        'response_time': avg_response_time,
        'optimization_time': avg_optimization_time,
        'error_rate': error_rate
    }
```

#### Database Maintenance
```bash
# Defragment SQLite database
sqlite3 data/feature11.db "VACUUM;"

# Check database integrity
sqlite3 data/feature11.db "PRAGMA integrity_check;"
```

#### Update Dependencies
```bash
# Check for updates
pip list --outdated

# Update if needed
pip install --upgrade requirements.txt
```

### Monthly Tasks

#### Archive Old Data
```python
def archive_old_data(days=90):
    """Archive allocations older than days"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Export to backup
    export_query = f"""
    SELECT * FROM allocations 
    WHERE created_date < '{cutoff_date}'
    """
    
    # Delete from main database
    delete_query = f"""
    DELETE FROM allocations 
    WHERE created_date < '{cutoff_date}'
    """
    
    logging.info(f"Archived {days}+ days of data")
```

#### Performance Optimization Review
```python
def optimize_system():
    """Review and optimize system configuration"""
    
    # 1. Review optimization weights
    # Are they still appropriate for current projects?
    
    # 2. Review cache settings
    # Is hit rate > 80%? If not, adjust duration
    
    # 3. Review timeout settings
    # Are optimizations completing within timeout?
    
    # 4. Review skill definitions
    # Are they still accurate?
    
    logging.info("Monthly optimization review complete")
```

#### Security Audit
```bash
# Check for exposed credentials
grep -r "password\|api_key\|secret" backend/ --exclude-dir=.git

# Review Monday.com API key usage
# Rotate if > 6 months old

# Check access logs
tail -1000 logs/phase11.log | grep "Unauthorized\|403\|401"
```

---

## User Management

### User Roles and Permissions

```
ADMIN (Full Access)
├── View all projects
├── Modify configurations
├── View all recommendations
├── Apply allocations
├── Manage users
└── View all reports

PROJECT_MANAGER
├── View own projects
├── View recommendations
├── Apply recommendations
└── View own reports

ANALYST
├── View own projects
├── View recommendations
└── Generate reports

VIEWER (Read-only)
└── View projects and metrics only
```

### API Key Management
```python
# Generate API key for user
def create_user_api_key(user_id, role):
    """Create API key for user"""
    import secrets
    
    api_key = secrets.token_urlsafe(32)
    
    # Store with user_id and permissions
    # Implement key rotation every 90 days
    
    return api_key

# Revoke API key
def revoke_api_key(api_key):
    """Revoke an API key"""
    # Mark as revoked
    # Audit log the revocation
    pass
```

---

## Data Management

### Data Backup

#### Automated Backup
```bash
#!/bin/bash
# backup_feature11.sh - Schedule with cron

BACKUP_DIR="/backup/feature11"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
cp data/feature11.db "$BACKUP_DIR/feature11_$DATE.db"

# Backup configuration
cp backend/app/phase11_config.py "$BACKUP_DIR/config_$DATE.py"

# Backup logs (optional)
gzip -c logs/phase11.log > "$BACKUP_DIR/logs_$DATE.tar.gz"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Restore from Backup
```bash
# Restore database
cp backup/feature11_YYYYMMDD_HHMMSS.db data/feature11.db

# Restore configuration
cp backup/config_YYYYMMDD_HHMMSS.py backend/app/phase11_config.py

# Restart service
systemctl restart feature11
```

### Data Export

#### Export Allocations
```python
def export_allocations(project_id, format='csv'):
    """Export allocations to file"""
    
    integration = create_resource_allocation_integration(project_id)
    allocations = integration.get_current_allocations()
    
    if format == 'csv':
        import csv
        with open(f'{project_id}_allocations.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'worker_id', 'start_date', 'end_date', 'hours'])
            writer.writeheader()
            writer.writerows(allocations)
    
    elif format == 'json':
        import json
        with open(f'{project_id}_allocations.json', 'w') as f:
            json.dump(allocations, f, indent=2)
    
    return f'{project_id}_allocations.{format}'
```

### Data Import

#### Import from External System
```python
def import_resources(file_path):
    """Import worker/resource data"""
    
    import csv
    import json
    
    if file_path.endswith('.csv'):
        with open(file_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create Worker object from row
                # Sync to system
                pass
    
    elif file_path.endswith('.json'):
        with open(file_path) as f:
            data = json.load(f)
            # Process JSON data
            # Sync to system
            pass
```

---

## Incident Response

### Critical Issues Response Plan

#### Issue: System Unresponsive

**Detection**: API /health endpoint returns 500

**Response**:
1. Check system resources
   ```bash
   top
   free -h
   df -h
   ```

2. Review recent logs
   ```bash
   tail -50 logs/phase11_errors.log
   ```

3. Restart service
   ```bash
   systemctl restart feature11
   ```

4. If still failing, check database
   ```bash
   sqlite3 data/feature11.db ".tables"
   ```

5. Escalate if necessary

#### Issue: Monday.com Sync Failure

**Detection**: No sync logs in last 30 minutes

**Response**:
1. Test API connectivity
   ```bash
   curl -H "Authorization: Bearer $API_KEY" https://api.monday.com/v2
   ```

2. Verify API key
   ```python
   from phase11_config import MONDAY_COM_CONFIG
   print(MONDAY_COM_CONFIG['api_key'])
   ```

3. Check workspace ID
4. Retry sync manually
   ```python
   integration = create_resource_allocation_integration("PRJ001")
   integration.sync_monday_com()
   ```

#### Issue: High Error Rate

**Detection**: Error rate > 5%

**Response**:
1. Check error logs
   ```bash
   grep ERROR logs/phase11_errors.log | tail -20
   ```

2. Identify error pattern
3. Review recent changes
4. Rollback if necessary
5. Document in incident log

### Escalation Policy

| Severity | Response Time | Escalation |
|----------|---------------|-----------|
| CRITICAL | Immediate | VP Technology |
| HIGH | 1 hour | Engineering Manager |
| MEDIUM | 4 hours | Team Lead |
| LOW | 24 hours | Team Member |

---

## Reporting

### Daily Report Template
```
FEATURE 11 DAILY REPORT
Date: YYYY-MM-DD

OPERATIONS SUMMARY:
- Total Projects: X
- Total Allocations: Y
- API Requests: Z

PERFORMANCE:
- Avg Response Time: XXms
- Cache Hit Rate: XX%
- Error Rate: X%

ISSUES:
- [List any issues]

MONDAY.COM SYNC:
- Status: Success/Failed
- Last Sync: HH:MM

ALERTS:
- [List any alerts]

ACTION ITEMS:
- [ ] Item 1
- [ ] Item 2
```

### Weekly Report
```
FEATURE 11 WEEKLY REPORT
Week: YYYY-MM-DD to YYYY-MM-DD

METRICS:
- Avg Utilization: XX%
- Total Conflicts: X
- Recommendations Generated: X
- Success Rate: XX%

TOP ISSUES:
1. Issue 1 - [Status]
2. Issue 2 - [Status]

PERFORMANCE TRENDS:
- Response Time: ↓ X% (better)
- Cache Hit Rate: ↑ X% (better)
- Error Rate: ◄► X% (stable)

RECOMMENDATIONS:
- [List recommendations]
```

### Monthly Management Report
```
FEATURE 11 MONTHLY REPORT
Month: YYYY-MM

EXECUTIVE SUMMARY:
- System Uptime: XX%
- Total Value Generated: $X
- User Satisfaction: XX%

KEY ACHIEVEMENTS:
- [Achievement 1]
- [Achievement 2]

AREAS FOR IMPROVEMENT:
- [Area 1]
- [Area 2]

BUDGET IMPACT:
- Costs: $X
- Savings Generated: $X
- ROI: XX%

NEXT MONTH PLAN:
- [Plan item 1]
- [Plan item 2]
```

---

## Standard Operating Procedures (SOPs)

### SOP 1: Daily System Check
**Time**: 09:00 AM
```bash
1. Check /health endpoint
2. Review error logs
3. Verify Monday.com sync
4. Check system resources
5. Document findings
```

### SOP 2: Weekly Maintenance
**Time**: Friday 3:00 PM
```bash
1. Generate weekly report
2. Archive old logs
3. Run database maintenance
4. Test backup/restore
5. Review performance metrics
```

### SOP 3: Monthly Optimization
**Time**: First Friday of month
```bash
1. Performance review
2. Configuration audit
3. Security check
4. Capacity planning
5. User feedback review
```

---

## Contact and Escalation

```
LEVEL 1 - SUPPORT (8am-5pm):
- Email: support@company.com
- Phone: 555-1234
- Response time: 1 hour

LEVEL 2 - ENGINEERING (on-call):
- Email: engineering@company.com
- Phone: 555-5678
- Response time: 30 minutes

LEVEL 3 - MANAGEMENT (critical only):
- Email: manager@company.com
- Phone: 555-9999
- Response time: 15 minutes
```

---

**Version**: 1.0  
**Last Updated**: Phase 23  
**Status**: Production Ready

# Feature 11: Resource Allocation - API Documentation

## Base URL
```
http://localhost:8000/api/v1/features/feature11
```

---

## Endpoints Overview

| # | Method | Endpoint | Purpose |
|---|--------|----------|---------|
| 1 | POST | `/projects/{id}/analyze` | Analyze and optimize project resources |
| 2 | GET | `/projects/{id}/recommendations` | Get allocation recommendations |
| 3 | GET | `/projects/{id}/resources` | List available resources |
| 4 | GET | `/projects/{id}/tasks` | List tasks needing allocation |
| 5 | GET | `/projects/{id}/allocations` | Get current allocations |
| 6 | POST | `/projects/{id}/allocations` | Create/apply new allocation |
| 7 | GET | `/projects/{id}/conflicts` | Detect resource conflicts |
| 8 | GET | `/projects/{id}/metrics` | Get allocation KPIs |
| 9 | GET | `/health` | Service health check |

---

## 1. Analyze Resources

### Endpoint
```
POST /api/v1/features/feature11/projects/{project_id}/analyze
```

### Description
Analyzes project resources and generates optimization recommendations based on specified goal.

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier (e.g., "PRJ001") |

### Request Body
```json
{
  "optimization_goal": "minimize_delay",
  "max_recommendations": 10,
  "allow_subcontractor_substitution": true
}
```

| Field | Type | Required | Values | Default | Description |
|-------|------|----------|--------|---------|-------------|
| `optimization_goal` | string | No | `minimize_delay`, `minimize_cost`, `balance` | `balance` | Optimization objective |
| `max_recommendations` | integer | No | 1-100 | 10 | Max recommendations to generate |
| `allow_subcontractor_substitution` | boolean | No | true, false | true | Allow subcontractor alternatives |

### Response (200 OK)
```json
{
  "success": true,
  "project_id": "PRJ001",
  "analysis_timestamp": "2024-02-05T10:30:00",
  "resource_status": "healthy",
  "optimization_goal": "minimize_delay",
  "confidence_score": 0.85,
  "total_recommendations": 5,
  "recommendations": [
    {
      "id": "REC-001",
      "title": "Allocate Worker W001 to Task TASK-001",
      "impact": "Reduces critical path by 2 days",
      "priority": "HIGH",
      "estimated_impact": {
        "delay_reduction_days": 2,
        "cost_change": 500
      }
    }
  ]
}
```

### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Operation success status |
| `project_id` | string | Project identifier |
| `analysis_timestamp` | string (ISO 8601) | When analysis was performed |
| `resource_status` | string | Overall status: "healthy", "warning", "critical" |
| `optimization_goal` | string | Selected optimization goal |
| `confidence_score` | number | Confidence in recommendations (0-1) |
| `total_recommendations` | integer | Number of recommendations generated |
| `recommendations` | array | List of recommendations |

### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Invalid optimization_goal: must be minimize_delay, minimize_cost, or balance"
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Project PRJ001 not found"
}
```

**500 Internal Server Error**
```json
{
  "success": false,
  "error": "Error analyzing resources: [details]"
}
```

### Examples

#### cURL
```bash
curl -X POST http://localhost:8000/api/v1/features/feature11/projects/PRJ001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "optimization_goal": "minimize_delay",
    "max_recommendations": 10,
    "allow_subcontractor_substitution": true
  }'
```

#### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/features/feature11/projects/PRJ001/analyze",
    json={
        "optimization_goal": "minimize_delay",
        "max_recommendations": 10,
        "allow_subcontractor_substitution": True
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Confidence: {result['confidence_score'] * 100:.0f}%")
```

---

## 2. Get Recommendations

### Endpoint
```
GET /api/v1/features/feature11/projects/{project_id}/recommendations
```

### Description
Retrieves detailed allocation recommendations for a project with optional filtering.

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |

### Query Parameters
| Parameter | Type | Default | Values | Description |
|-----------|------|---------|--------|-------------|
| `limit` | integer | 10 | 1-100 | Max recommendations to return |
| `priority` | string | null | `HIGH`, `MEDIUM`, `LOW` | Filter by priority |
| `type` | string | null | `allocation`, `subcontractor`, `crew`, etc | Filter by type |

### Response (200 OK)
```json
{
  "success": true,
  "project_id": "PRJ001",
  "total_recommendations": 5,
  "recommendations": [
    {
      "id": "REC-001",
      "type": "allocation",
      "title": "Allocate Worker W001 to Task TASK-001",
      "description": "Worker has required carpentry skills (senior level)",
      "impact": "Reduces critical path by 2 days",
      "priority": "HIGH",
      "confidence": 0.92,
      "estimated_impact": {
        "delay_reduction_days": 2,
        "cost_change": 500,
        "risk_reduction": 0.15
      },
      "implementation_steps": [
        "Verify worker W001 has no conflicts",
        "Confirm availability Feb 1-6",
        "Update task allocation in system"
      ],
      "monday_com_actions": [
        "Update worker assignment in monday.com",
        "Add worker to task team",
        "Update timeline view"
      ]
    }
  ]
}
```

### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique recommendation identifier |
| `type` | string | Recommendation type |
| `title` | string | Short description |
| `description` | string | Detailed explanation |
| `impact` | string | Expected impact summary |
| `priority` | string | HIGH, MEDIUM, or LOW |
| `confidence` | number | Confidence score (0-1) |
| `estimated_impact` | object | Quantified impacts |
| `implementation_steps` | array | Steps to implement |
| `monday_com_actions` | array | Monday.com sync actions |

### Examples

#### Get all high-priority recommendations
```bash
curl "http://localhost:8000/api/v1/features/feature11/projects/PRJ001/recommendations?priority=HIGH&limit=10"
```

#### Get allocation recommendations only
```bash
curl "http://localhost:8000/api/v1/features/feature11/projects/PRJ001/recommendations?type=allocation"
```

---

## 3. List Resources

### Endpoint
```
GET /api/v1/features/feature11/projects/{project_id}/resources
```

### Description
Lists all available resources for a project (workers, crews, subcontractors).

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | string | null | Filter: `workers`, `crews`, `subcontractors` |
| `skill` | string | null | Filter by skill name |
| `status` | string | null | Filter: `available`, `allocated`, `unavailable` |

### Response (200 OK)
```json
{
  "success": true,
  "project_id": "PRJ001",
  "total_workers": 15,
  "total_crews": 3,
  "total_subcontractors": 5,
  "workers": [
    {
      "worker_id": "W001",
      "name": "John Smith",
      "skills": ["carpentry:senior", "site_management:intermediate"],
      "availability": {
        "hours_per_week": 40,
        "available_from": "2024-01-01",
        "available_to": "2024-12-31",
        "max_concurrent_tasks": 2
      },
      "hourly_rate": 55,
      "reliability": 0.88,
      "current_allocations": 1,
      "unallocated_hours": 32
    }
  ],
  "crews": [
    {
      "crew_id": "C001",
      "name": "Carpentry Team Alpha",
      "lead_worker_id": "W001",
      "member_count": 3,
      "combined_reliability": 0.85
    }
  ],
  "subcontractors": [
    {
      "subcontractor_id": "SUB001",
      "company_name": "Premier Electrical",
      "services": ["electrical", "low_voltage"],
      "hourly_rate": 85,
      "performance_score": 0.92,
      "availability": "high"
    }
  ]
}
```

---

## 4. List Tasks

### Endpoint
```
GET /api/v1/features/feature11/projects/{project_id}/tasks
```

### Description
Lists all tasks needing resource allocation.

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | null | Filter: `unallocated`, `partially_allocated`, `allocated`, `completed` |
| `critical_path` | boolean | null | Filter: true/false |

### Response (200 OK)
```json
{
  "success": true,
  "project_id": "PRJ001",
  "total_tasks": 42,
  "tasks": [
    {
      "task_id": "TASK-001",
      "title": "Foundation Work",
      "required_role": "carpentry",
      "required_skills": ["carpentry:senior"],
      "workers_needed": 3,
      "duration_days": 5,
      "estimated_hours": 120,
      "start_date": "2024-02-01",
      "end_date": "2024-02-06",
      "critical_path": true,
      "allocation_status": "partially_allocated",
      "allocated_workers": 2,
      "unallocated_slots": 1
    }
  ]
}
```

---

## 5. Get Allocations

### Endpoint
```
GET /api/v1/features/feature11/projects/{project_id}/allocations
```

### Description
Lists current resource allocations for a project.

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | null | Filter: `active`, `pending`, `completed` |
| `worker_id` | string | null | Filter by worker |
| `task_id` | string | null | Filter by task |

### Response (200 OK)
```json
{
  "success": true,
  "project_id": "PRJ001",
  "total_allocations": 42,
  "allocations": [
    {
      "allocation_id": "ALLOC-001",
      "task_id": "TASK-001",
      "worker_id": "W001",
      "worker_name": "John Smith",
      "start_date": "2024-02-01",
      "end_date": "2024-02-06",
      "hours": 40,
      "status": "active",
      "created_date": "2024-01-25"
    }
  ]
}
```

---

## 6. Apply Allocation

### Endpoint
```
POST /api/v1/features/feature11/projects/{project_id}/allocations
```

### Description
Creates and applies a new resource allocation.

### Request Body
```json
{
  "task_id": "TASK-001",
  "worker_id": "W001",
  "duration_days": 5,
  "start_date": "2024-02-01"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | Yes | Task to allocate to |
| `worker_id` | string | Yes | Worker to allocate |
| `duration_days` | integer | Yes | Duration of allocation |
| `start_date` | string (YYYY-MM-DD) | Yes | Start date |

### Response (201 Created)
```json
{
  "success": true,
  "allocation_id": "ALLOC-NEW-001",
  "summary": "Successfully allocated W001 to TASK-001 for 5 days"
}
```

### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Worker W001 has skill mismatch: requires senior carpentry"
}
```

---

## 7. Get Conflicts

### Endpoint
```
GET /api/v1/features/feature11/projects/{project_id}/conflicts
```

### Description
Identifies resource allocation conflicts and issues.

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `severity` | string | null | Filter: `critical`, `high`, `medium`, `low` |

### Response (200 OK)
```json
{
  "success": true,
  "project_id": "PRJ001",
  "total_conflicts": 3,
  "conflicts": [
    {
      "conflict_id": "CONFLICT-001",
      "type": "overallocation",
      "severity": "critical",
      "details": "Worker W001 allocated to 3 concurrent tasks (max: 2)",
      "affected_resources": ["W001", "TASK-001", "TASK-002", "TASK-003"],
      "suggested_resolution": "Move TASK-003 to alternative worker or reschedule"
    }
  ]
}
```

---

## 8. Get Metrics

### Endpoint
```
GET /api/v1/features/feature11/projects/{project_id}/metrics
```

### Description
Retrieves allocation metrics and KPIs.

### Response (200 OK)
```json
{
  "success": true,
  "project_id": "PRJ001",
  "metrics": {
    "total_workers": 15,
    "total_crews": 3,
    "total_subcontractors": 5,
    "average_utilization": 0.82,
    "unallocated_hours": 120,
    "estimated_delay_risk": 0.25,
    "estimated_cost_variance": 0.08,
    "critical_skills_gap": ["electrical:senior"],
    "allocation_efficiency": 0.88,
    "conflict_count": 3,
    "compliance_status": "on_track"
  }
}
```

| Metric | Type | Range | Meaning |
|--------|------|-------|---------|
| `average_utilization` | number | 0-1 | % of work assigned vs available |
| `unallocated_hours` | integer | >0 | Hours without assignment |
| `estimated_delay_risk` | number | 0-1 | Risk of schedule delay |
| `estimated_cost_variance` | number | 0-1 | Variance from budget estimate |
| `compliance_status` | string | - | "on_track", "at_risk", "critical" |

---

## 9. Health Check

### Endpoint
```
GET /api/v1/features/feature11/health
```

### Description
Service health check endpoint.

### Response (200 OK)
```json
{
  "status": "healthy",
  "service": "Feature 11 - Resource Allocation",
  "version": "1.0.0"
}
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Resource retrieved |
| 201 | Created | Allocation created |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Project/resource not found |
| 500 | Server Error | Unexpected error |

### Error Response Format
```json
{
  "success": false,
  "error": "Detailed error message"
}
```

---

## Rate Limiting

- **Limit**: 1000 requests/minute per API key
- **Headers**: Returned in response headers
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## Authentication

All endpoints require authentication. Include API key in header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/...
```

---

## Pagination

For endpoints that return lists, use pagination:

```bash
GET /api/v1/features/feature11/projects/{id}/allocations?limit=20&offset=0
```

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| `limit` | integer | 10 | 100 |
| `offset` | integer | 0 | - |

---

## Date and Time Formats

- **Dates**: `YYYY-MM-DD` (e.g., "2024-02-05")
- **Timestamps**: ISO 8601 (e.g., "2024-02-05T10:30:00")

---

## SDK Examples

### JavaScript/Node.js
```javascript
const axios = require('axios');

const analyzeResources = async (projectId) => {
  const response = await axios.post(
    `http://localhost:8000/api/v1/features/feature11/projects/${projectId}/analyze`,
    { optimization_goal: 'minimize_delay', max_recommendations: 10 }
  );
  return response.data;
};
```

### Python
```python
import requests

def analyze_resources(project_id):
    url = f"http://localhost:8000/api/v1/features/feature11/projects/{project_id}/analyze"
    payload = {
        "optimization_goal": "minimize_delay",
        "max_recommendations": 10
    }
    response = requests.post(url, json=payload)
    return response.json()
```

---

## Useful Resources

- [API Response Examples](#)
- [Error Codes Reference](#)
- [Rate Limiting Policy](#)
- [Authentication Guide](#)
- [Webhook Documentation](#)

---

**API Version**: 1.0  
**Last Updated**: Phase 23  
**Status**: Production Ready

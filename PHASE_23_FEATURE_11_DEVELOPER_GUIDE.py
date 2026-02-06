"""
Feature 11: Resource Allocation - Developer Usage Guide
Complete guide for developers using Feature 11 capabilities
"""

# ============================================================================
# SECTION 1: BASIC CONCEPTS
# ============================================================================

"""
KEY CONCEPTS IN FEATURE 11:

1. RESOURCES
   - Workers: Individual employees with skills and availability
   - Crews: Teams of workers with a lead
   - Subcontractors: Third-party service providers

2. ALLOCATION
   - Assigning resources to tasks
   - Managing skill matching
   - Handling availability conflicts

3. OPTIMIZATION
   - Minimize delay: Reduce critical path
   - Minimize cost: Reduce project costs
   - Balance: Equal weight to both factors

4. RECOMMENDATIONS
   - Actionable suggestions from analysis
   - Scored by impact and confidence
   - Can be applied to modify allocations
"""

# ============================================================================
# SECTION 2: QUICK START
# ============================================================================

from phase11_resource_types import (
    Worker, Skill, SkillLevel, ResourceAvailability,
    AllocationRequest
)
from phase11_resource_integration import (
    create_resource_allocation_integration,
    analyze_project_resources,
    generate_allocation_recommendations
)
from datetime import date

# Step 1: Create integration for your project
project_id = "my_project_001"
integration = create_resource_allocation_integration(project_id)

# Step 2: Request resource analysis
request = AllocationRequest(
    project_id=project_id,
    optimization_goal="minimize_delay",  # or "minimize_cost" or "balance"
    max_recommendations=10,
    allow_subcontractor_substitution=True
)

# Step 3: Analyze and get recommendations
result = analyze_project_resources(integration, request)

print(f"Analysis Complete!")
print(f"Confidence: {result.confidence_score * 100:.1f}%")
print(f"Recommendations: {len(result.recommendations)}")

# Step 4: Review top recommendations
for rec in result.recommendations[:5]:
    print(f"\n[{rec['priority']}] {rec['title']}")
    print(f"Impact: {rec['estimated_impact']}")


# ============================================================================
# SECTION 3: WORKING WITH WORKERS
# ============================================================================

# Create a worker with multiple skills
carpenter = Worker(
    worker_id="W001",
    name="John Smith",
    crew_id="C001",  # Part of carpentry crew
    skills=[
        Skill(
            skill_name="carpentry",
            level=SkillLevel.SENIOR,
            years_experience=10,
            certifications_required=False
        ),
        Skill(
            skill_name="site_management",
            level=SkillLevel.INTERMEDIATE,
            years_experience=5,
            certifications_required=True
        )
    ],
    availability=ResourceAvailability(
        available_from=date(2024, 1, 1),
        available_to=date(2024, 12, 31),
        hours_per_week=40,
        max_concurrent_tasks=2,
        on_site_requirement=True,
        travel_time_hours=0.5
    ),
    hourly_rate=55.00,
    base_reliability_score=0.88,
    absence_history=[],  # Track historical absences
    monday_user_id="user_001",
)

# Access worker information
print(f"Worker: {carpenter.name}")
print(f"Hourly Rate: ${carpenter.hourly_rate}")
print(f"Reliability: {carpenter.base_reliability_score * 100:.0f}%")
print(f"Skills: {[s.skill_name for s in carpenter.skills]}")


# ============================================================================
# SECTION 4: WORKING WITH CREWS
# ============================================================================

from phase11_resource_types import Crew

# Create a crew
carpentry_crew = Crew(
    crew_id="C001",
    name="Carpentry Team Alpha",
    lead_worker_id="W001",  # John Smith is the lead
    member_worker_ids=["W001", "W002", "W003"],
    team_role="carpentry",
    combined_reliability_score=0.85,
    monday_team_id="team_001",
)

# Access crew information
print(f"\nCrew: {carpentry_crew.name}")
print(f"Members: {len(carpentry_crew.member_worker_ids)}")
print(f"Lead: {carpentry_crew.lead_worker_id}")
print(f"Reliability: {carpentry_crew.combined_reliability_score * 100:.0f}%")


# ============================================================================
# SECTION 5: WORKING WITH SUBCONTRACTORS
# ============================================================================

from phase11_resource_types import Subcontractor

# Create a subcontractor for when internal resources are unavailable
electrical_contractor = Subcontractor(
    subcontractor_id="SUB001",
    company_name="Premier Electrical Solutions",
    primary_contact="Jane Doe",
    contact_phone="555-0123",
    services=["electrical", "low_voltage", "fiber_optic"],
    availability=ResourceAvailability(
        available_from=date(2024, 1, 1),
        available_to=date(2024, 12, 31),
        hours_per_week=999,  # Essentially unlimited
        max_concurrent_tasks=10,
        on_site_requirement=False,
        travel_time_hours=1
    ),
    hourly_rate=85.00,
    contract_cost_range=(5000, 15000),
    performance_score=0.92,
    reliability_score=0.90,
    past_delay_frequency=0.02,
    past_cost_overrun_percent=0.05,
    monday_vendor_id="vendor_001",
)

# Access subcontractor information
print(f"\nSubcontractor: {electrical_contractor.company_name}")
print(f"Services: {electrical_contractor.services}")
print(f"Performance Score: {electrical_contractor.performance_score * 100:.0f}%")
print(f"Cost Range: ${electrical_contractor.contract_cost_range[0]} - ${electrical_contractor.contract_cost_range[1]}")


# ============================================================================
# SECTION 6: RESOURCE ALLOCATION CONSTRAINTS
# ============================================================================

"""
UNDERSTANDING CONSTRAINTS:

1. SKILL MATCHING
   - A worker's skill level must match or exceed task requirements
   - Example: Task needs SENIOR carpentry, worker has INTERMEDIATE -> FAIL

2. AVAILABILITY
   - Task dates must be within resource availability window
   - Example: Task Feb 1-10, worker available Feb 5-20 -> CONFLICT

3. CONCURRENT TASKS
   - Resource can't exceed max concurrent tasks
   - Example: Worker max=2, already on 2 tasks, can't add more -> OVERALLOCATION

4. ON-SITE REQUIREMENT
   - Some resources must be on-site for certain tasks
   - Some resources can work remotely
   - Example: Site supervision task requires on-site -> CONSTRAINT

5. TRAVEL TIME
   - Account for travel time between sites
   - Example: Worker needs 1 hour travel, 8 hour task -> 9 hours budget needed
"""

from phase11_resource_types import TaskResourceRequirement

# Define a task with specific requirements
foundation_task = TaskResourceRequirement(
    task_id="TASK-F001",
    required_role="carpentry",
    required_skills=[
        Skill(
            skill_name="carpentry",
            level=SkillLevel.SENIOR,  # Need senior level
            years_experience=0,
            certifications_required=False
        )
    ],
    min_skill_level=SkillLevel.SENIOR,
    workers_needed=3,
    crew_size_optimal=3,  # Optimal to use full crew
    can_use_subcontractor=False,  # Must use internal resources
    duration_days=5,
    start_date=date(2024, 2, 1),
    end_date=date(2024, 2, 6),
    critical_path=True,  # On critical path - impacts schedule
    estimated_hours=120,  # 3 workers * 40 hours
)

print(f"\nTask: {foundation_task.task_id}")
print(f"Role: {foundation_task.required_role}")
print(f"Workers Needed: {foundation_task.workers_needed}")
print(f"Duration: {foundation_task.duration_days} days")
print(f"Critical Path: {foundation_task.critical_path}")


# ============================================================================
# SECTION 7: ALLOCATION ANALYSIS
# ============================================================================

# Analyze resources for a project
def analyze_project_allocations(project_id):
    """Complete analysis workflow"""
    
    # Step 1: Create integration
    integration = create_resource_allocation_integration(project_id)
    
    # Step 2: Get monday.com data
    monday_data = integration.get_monday_com_data()
    print(f"Loaded {len(monday_data.get('workers', []))} workers")
    print(f"Loaded {len(monday_data.get('crews', []))} crews")
    
    # Step 3: Request analysis with specific goal
    request = AllocationRequest(
        project_id=project_id,
        optimization_goal="minimize_delay",
        max_recommendations=15,
        allow_subcontractor_substitution=True
    )
    
    # Step 4: Run analysis
    result = analyze_project_resources(integration, request)
    
    # Step 5: Review results
    print(f"\n=== ALLOCATION ANALYSIS RESULTS ===")
    print(f"Project: {result.project_id}")
    print(f"Optimization Goal: {result.optimization_goal}")
    print(f"Confidence Score: {result.confidence_score * 100:.1f}%")
    print(f"Total Recommendations: {len(result.recommendations)}")
    
    # Step 6: Get detailed recommendations
    recommendations = generate_allocation_recommendations(
        integration,
        project_id=project_id,
        max_recommendations=10
    )
    
    return {
        'result': result,
        'recommendations': recommendations,
        'integration': integration
    }

# Run analysis
analysis = analyze_project_allocations("PRJ001")


# ============================================================================
# SECTION 8: REVIEWING RECOMMENDATIONS
# ============================================================================

"""
RECOMMENDATION TYPES:

1. WORKER ALLOCATION
   "Allocate W001 to TASK-001"
   - Direct assignment of worker to task
   - Includes time and date information
   - Estimated impact on schedule and cost

2. CREW ASSIGNMENT
   "Assign crew C001 to phase P002"
   - Allocate entire crew as a unit
   - Efficient for team-based work
   - Better crew dynamics

3. SKILL DEVELOPMENT
   "Train W002 in carpentry:senior"
   - Recommendation to upskill worker
   - Suitable for future tasks
   - Long-term investment

4. SUBCONTRACTOR USE
   "Use SUB001 for electrical work"
   - Alternative when internal resources unavailable
   - Good for specialty work
   - May have different cost/quality profile

5. LOAD BALANCING
   "Redistribute tasks to balance W001 and W002"
   - Improve overall utilization
   - Prevent overallocation
   - Better resource efficiency

6. TIMELINE ADJUSTMENT
   "Reschedule TASK-002 to Feb 15"
   - Move task to accommodate resources
   - Resolve conflicts
   - May impact other tasks
"""

def review_recommendations(integration, project_id):
    """Review and prioritize recommendations"""
    
    recommendations = generate_allocation_recommendations(
        integration,
        project_id=project_id,
        max_recommendations=20
    )
    
    # Group by priority
    high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
    medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']
    low_priority = [r for r in recommendations if r['priority'] == 'LOW']
    
    print(f"\n=== RECOMMENDATIONS BY PRIORITY ===")
    print(f"High Priority: {len(high_priority)}")
    print(f"Medium Priority: {len(medium_priority)}")
    print(f"Low Priority: {len(low_priority)}")
    
    # Review high priority
    print(f"\n=== TOP HIGH PRIORITY RECOMMENDATIONS ===")
    for i, rec in enumerate(high_priority[:5], 1):
        print(f"\n{i}. {rec['title']}")
        print(f"   Type: {rec.get('type', 'allocation')}")
        print(f"   Impact: {rec.get('estimated_impact')}")
        print(f"   Confidence: {rec.get('confidence', 0) * 100:.0f}%")
        print(f"   Description: {rec.get('description', 'N/A')}")


# ============================================================================
# SECTION 9: APPLYING ALLOCATIONS
# ============================================================================

def apply_recommendation(integration, task_id, worker_id, duration_days, start_date):
    """Apply a particular allocation recommendation"""
    
    try:
        # Apply the allocation
        result = integration.apply_allocation(
            task_id=task_id,
            worker_id=worker_id,
            start_date=start_date,
            duration_days=duration_days
        )
        
        if result['success']:
            print(f"✓ Allocation created: {result['allocation_id']}")
            print(f"  Summary: {result['summary']}")
            
            # Get updated metrics
            updated_metrics = integration.get_allocation_metrics()
            print(f"\nUpdated Metrics:")
            print(f"  Utilization: {updated_metrics.get('average_utilization', 0) * 100:.0f}%")
            print(f"  Unallocated Hours: {updated_metrics.get('unallocated_hours', 0)}")
            
            return True
        else:
            print(f"✗ Allocation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"✗ Error applying allocation: {str(e)}")
        return False

# Example usage:
# apply_recommendation(
#     integration,
#     task_id="TASK-001",
#     worker_id="W001",
#     duration_days=5,
#     start_date=date(2024, 2, 1)
# )


# ============================================================================
# SECTION 10: HANDLING CONFLICTS
# ============================================================================

"""
COMMON ALLOCATION CONFLICTS:

1. SKILL MISMATCH
   Problem: Worker doesn't have required skill level
   Resolution: Either find different worker or use subcontractor

2. AVAILABILITY GAP
   Problem: Worker not available during task period
   Resolution: Reschedule task or find different worker

3. OVERALLOCATION
   Problem: Worker already at max concurrent tasks
   Resolution: Redistribute tasks or use different worker

4. COST CONCERN
   Problem: Allocation exceeds budget for task
   Resolution: Use lower-cost subcontractor or reduce scope

5. WORK LOCATION
   Problem: Task on-site but worker works remotely
   Resolution: Find different worker or reschedule

6. LOAD IMBALANCE
   Problem: Some workers overallocated, others underutilized
   Resolution: Rebalance task assignments
"""

def detect_and_resolve_conflicts(integration, project_id):
    """Detect and suggest resolutions for conflicts"""
    
    conflicts = integration.get_resource_conflicts()
    
    print(f"\n=== RESOURCE CONFLICTS DETECTED ===")
    print(f"Total Conflicts: {len(conflicts)}")
    
    # Group by severity
    critical = [c for c in conflicts if c.get('severity') == 'critical']
    high = [c for c in conflicts if c.get('severity') == 'high']
    medium = [c for c in conflicts if c.get('severity') == 'medium']
    low = [c for c in conflicts if c.get('severity') == 'low']
    
    print(f"Critical: {len(critical)}")
    print(f"High: {len(high)}")
    print(f"Medium: {len(medium)}")
    print(f"Low: {len(low)}")
    
    # Review critical conflicts
    if critical:
        print(f"\n=== CRITICAL CONFLICTS ===")
        for conflict in critical:
            print(f"\nConflict: {conflict.get('conflict_id')}")
            print(f"Type: {conflict.get('type')}")
            print(f"Details: {conflict.get('details')}")
            print(f"Suggested Resolution: {conflict.get('suggested_resolution')}")


# ============================================================================
# SECTION 11: USING THE API
# ============================================================================

"""
REST API ENDPOINTS FOR FEATURE 11:

Endpoint: POST /api/v1/features/feature11/projects/{id}/analyze
Purpose: Analyze and optimize project resources
Request:
{
    "optimization_goal": "minimize_delay",
    "max_recommendations": 10,
    "allow_subcontractor_substitution": true
}
Response:
{
    "success": true,
    "project_id": "PRJ001",
    "confidence_score": 0.85,
    "total_recommendations": 5,
    "recommendations": [...]
}

---

Endpoint: GET /api/v1/features/feature11/projects/{id}/recommendations
Purpose: Get detailed recommendations
Query Parameters:
  - limit: max results (default 10)
  - priority: filter by HIGH|MEDIUM|LOW
  - type: filter by type
Response:
{
    "success": true,
    "total_recommendations": 5,
    "recommendations": [...]
}

---

Endpoint: GET /api/v1/features/feature11/projects/{id}/resources
Purpose: Get available resources
Response:
{
    "success": true,
    "total_workers": 15,
    "total_crews": 3,
    "total_subcontractors": 5,
    "workers": [...],
    "crews": [...],
    "subcontractors": [...]
}

---

Endpoint: GET /api/v1/features/feature11/projects/{id}/allocations
Purpose: Get current allocations
Response:
{
    "success": true,
    "total_allocations": 42,
    "allocations": [...]
}

---

Endpoint: POST /api/v1/features/feature11/projects/{id}/allocations
Purpose: Apply/create allocation
Request:
{
    "task_id": "TASK-001",
    "worker_id": "W001",
    "duration_days": 5,
    "start_date": "2024-02-01"
}
Response:
{
    "success": true,
    "allocation_id": "ALLOC-NEW-001",
    "summary": "..."
}

---

Endpoint: GET /api/v1/features/feature11/projects/{id}/conflicts
Purpose: Get resource conflicts
Response:
{
    "success": true,
    "total_conflicts": 3,
    "conflicts": [...]
}

---

Endpoint: GET /api/v1/features/feature11/projects/{id}/metrics
Purpose: Get allocation metrics
Response:
{
    "success": true,
    "metrics": {
        "average_utilization": 0.82,
        "unallocated_hours": 120,
        "compliance_status": "on_track"
    }
}
"""

# Example API usage:
import requests

def call_analyze_api(project_id):
    """Call analysis API endpoint"""
    
    url = f"http://localhost:8000/api/v1/features/feature11/projects/{project_id}/analyze"
    
    payload = {
        "optimization_goal": "minimize_delay",
        "max_recommendations": 10,
        "allow_subcontractor_substitution": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Analysis Results:")
            print(f"  Confidence: {data['confidence_score'] * 100:.1f}%")
            print(f"  Recommendations: {data['total_recommendations']}")
            return data
        else:
            print(f"API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Connection Error: {str(e)}")
        return None


# ============================================================================
# SECTION 12: BEST PRACTICES
# ============================================================================

"""
BEST PRACTICES FOR RESOURCE ALLOCATION:

1. REGULAR ANALYSIS
   - Run analysis weekly or before major milestones
   - Monitor changes in resource availability
   - Track actual vs. planned allocations

2. CONFLICT RESOLUTION
   - Address conflicts immediately when detected
   - Escalate critical conflicts to project manager
   - Document resolutions for future reference

3. SKILL DEVELOPMENT
   - Invest in upskilling workers for future projects
   - Consider training recommendations
   - Build team capability over time

4. SUBCONTRACTOR USE
   - Use subcontractors strategically for specialty work
   - Maintain relationships with reliable vendors
   - Balance cost vs. quality tradeoffs

5. TEAM COHESION
   - Keep crews together when possible
   - Minimize frequent reassignments
   - Consider team dynamics in allocations

6. DOCUMENTATION
   - Document all allocation decisions
   - Track reasons for deviations
   - Use for continuous improvement

7. OPTIMIZATION GOALS
   - Choose appropriate optimization goal per project
   - Adjust goals as project progresses
   - Balance short-term and long-term objectives

8. MONDAY.COM SYNC
   - Keep worker/crew data current in monday.com
   - Sync allocations back to monday.com
   - Use monday.com as source of truth
"""

# ============================================================================
# SECTION 13: TROUBLESHOOTING
# ============================================================================

"""
TROUBLESHOOTING GUIDE:

PROBLEM: "No recommendations generated"
CAUSES:
  - Project already fully allocated
  - Insufficient resource availability
  - No conflicts detected
SOLUTIONS:
  - Consider extending project timeline
  - Bring in additional resources
  - Review allocation constraints

PROBLEM: "Recommendations have low confidence"
CAUSES:
  - Uncertain data quality
  - Many edge cases
  - Complex constraints
SOLUTIONS:
  - Verify worker/task data accuracy
  - Simplify constraints if possible
  - Manual review and adjustment

PROBLEM: "Allocation fails when applied"
CAUSES:
  - Constraint violation
  - Data changed since analysis
  - Worker no longer available
SOLUTIONS:
  - Refresh analysis
  - Check worker availability
  - Try alternative recommendation

PROBLEM: "Monday.com sync not working"
CAUSES:
  - Invalid API credentials
  - Network connectivity
  - Permission issues
SOLUTIONS:
  - Verify API credentials
  - Check network connection
  - Review monday.com permissions

PROBLEM: "Slow optimization performance"
CAUSES:
  - Large project (1000+ tasks)
  - Complex constraints
  - Insufficient resources
SOLUTIONS:
  - Increase timeout
  - Simplify optimization goal
  - Use subcontractor for some tasks
"""

# ============================================================================
# SECTION 14: COMPLETE EXAMPLE WORKFLOW
# ============================================================================

def complete_allocation_workflow(project_id):
    """
    Complete workflow for resource allocation:
    1. Set up integration
    2. Analyze resources
    3. Get recommendations
    4. Detect conflicts
    5. Apply top recommendations
    6. Monitor metrics
    """
    
    print(f"\n{'='*60}")
    print(f"COMPLETE ALLOCATION WORKFLOW: {project_id}")
    print(f"{'='*60}")
    
    # Step 1: Setup
    print(f"\n1. Setting up integration...")
    integration = create_resource_allocation_integration(project_id)
    print(f"   ✓ Integration ready")
    
    # Step 2: Analyze
    print(f"\n2. Analyzing resources...")
    request = AllocationRequest(
        project_id=project_id,
        optimization_goal="minimize_delay",
        max_recommendations=15,
        allow_subcontractor_substitution=True
    )
    result = analyze_project_resources(integration, request)
    print(f"   ✓ Analysis complete (Confidence: {result.confidence_score * 100:.0f}%)")
    
    # Step 3: Get recommendations
    print(f"\n3. Generating recommendations...")
    recommendations = generate_allocation_recommendations(
        integration,
        project_id=project_id,
        max_recommendations=10
    )
    print(f"   ✓ Generated {len(recommendations)} recommendations")
    
    # Step 4: Detect conflicts
    print(f"\n4. Detecting conflicts...")
    conflicts = integration.get_resource_conflicts()
    print(f"   ✓ Found {len(conflicts)} conflicts")
    
    # Step 5: Apply top recommendations
    print(f"\n5. Applying top recommendations...")
    applied_count = 0
    for rec in recommendations[:5]:
        if rec.get('type') == 'allocation':
            # Try to apply
            success = apply_recommendation(
                integration,
                task_id=rec.get('task_id'),
                worker_id=rec.get('worker_id'),
                duration_days=rec.get('duration_days'),
                start_date=rec.get('start_date')
            )
            if success:
                applied_count += 1
    print(f"   ✓ Applied {applied_count} recommendations")
    
    # Step 6: Monitor metrics
    print(f"\n6. Monitoring metrics...")
    metrics = integration.get_allocation_metrics()
    print(f"   ✓ Utilization: {metrics.get('average_utilization', 0) * 100:.0f}%")
    print(f"   ✓ Unallocated Hours: {metrics.get('unallocated_hours', 0)}")
    print(f"   ✓ Compliance: {metrics.get('compliance_status', 'unknown')}")
    
    print(f"\n{'='*60}")
    print(f"WORKFLOW COMPLETE")
    print(f"{'='*60}")


# Run complete workflow
# complete_allocation_workflow("PRJ001")


# ============================================================================
# SECTION 15: REFERENCE
# ============================================================================

"""
QUICK REFERENCE:

Core Classes:
  - Worker: Individual employee resource
  - Crew: Team of workers
  - Subcontractor: Third-party service provider
  - Skill: Worker competency in specific area
  - ResourceAvailability: Time/capacity constraints
  - TaskResourceRequirement: Task-specific needs
  
Key Functions:
  - create_resource_allocation_integration(): Setup integration
  - analyze_project_resources(): Run optimization
  - generate_allocation_recommendations(): Get suggestions
  - apply_allocation(): Create allocation

Optimization Goals:
  - "minimize_delay": Reduce critical path
  - "minimize_cost": Minimize project cost
  - "balance": Equal weight to delay and cost

Constraints:
  - Skill level matching
  - Availability windows
  - Concurrent task limits
  - On-site requirements
  - Travel time considerations

Recommendation Types:
  - worker_allocation: Assign worker to task
  - crew_assignment: Assign crew to phase
  - subcontractor_use: Hire external resource
  - skill_development: Upskill worker
  - load_balancing: Redistribute work
  - timeline_adjustment: Reschedule task

Severity Levels:
  - CRITICAL: Must resolve immediately
  - HIGH: Should resolve soon
  - MEDIUM: Should address
  - LOW: Nice to address
"""

if __name__ == "__main__":
    print("Feature 11 - Resource Allocation Developer Guide")
    print("See sections above for detailed usage examples")

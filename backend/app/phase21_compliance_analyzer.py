"""Phase 21 - Compliance & Safety Analyzer

Analyzes safety incidents, compliance assessments, and projects regulatory risk.
Provides audit-ready outputs and schedule/cost impact estimates.

Demo mode: Uses synthetic compliance and incident data.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random

from phase21_compliance_types import (
    SafetyIncident,
    ComplianceCheckpoint,
    ComplianceAssessment,
    SafetyRiskScore,
    ProjectComplianceSafety,
)


class ComplianceSafetyAnalyzer:
    """Analyzes safety incidents and compliance status."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    @staticmethod
    def standard_checkpoints() -> List[ComplianceCheckpoint]:
        """Return standard compliance checkpoints for construction projects.
        
        Returns:
            List of compliance requirements
        """
        return [
            ComplianceCheckpoint(
                checkpoint_id="OSHA_1",
                category="site_safety",
                title="Fall Protection Systems",
                description="All workers on heights >6 feet must have fall protection",
                requirement_id="OSHA 1926.502",
            ),
            ComplianceCheckpoint(
                checkpoint_id="OSHA_2",
                category="site_safety",
                title="Scaffolding Safety",
                description="Scaffold installation and maintenance per OSHA standards",
                requirement_id="OSHA 1926.451",
            ),
            ComplianceCheckpoint(
                checkpoint_id="OSHA_3",
                category="site_safety",
                title="Personal Protective Equipment (PPE)",
                description="Required PPE provided and worn on site",
                requirement_id="OSHA 1926.95",
            ),
            ComplianceCheckpoint(
                checkpoint_id="ENV_1",
                category="environmental",
                title="Stormwater Management",
                description="Stormwater pollution prevention plan in place",
                requirement_id="EPA NPDES",
            ),
            ComplianceCheckpoint(
                checkpoint_id="LABOR_1",
                category="labor",
                title="Payroll & Wage Documentation",
                description="Prevailing wage documentation and payroll records maintained",
                requirement_id="FLSA Davis-Bacon",
            ),
            ComplianceCheckpoint(
                checkpoint_id="BUILD_1",
                category="structural",
                title="Structural Inspections",
                description="Third-party structural inspections completed per schedule",
                requirement_id="IBC 2021",
            ),
        ]
    
    def assess_compliance(
        self,
        project_id: str,
        checkpoints: List[ComplianceCheckpoint],
        known_assessments: Optional[List[ComplianceAssessment]] = None,
    ) -> List[ComplianceAssessment]:
        """Assess compliance status for checkpoints.
        
        Args:
            project_id: Project identifier
            checkpoints: List of checkpoints to assess
            known_assessments: Pre-loaded assessments (for production); if None, generates demo
        
        Returns:
            List of compliance assessments
        """
        if known_assessments:
            return known_assessments
        
        # Demo mode: generate synthetic assessments
        assessments = []
        random.seed(hash(project_id) % (2**31))
        
        for checkpoint in checkpoints:
            # Stochastic: most checkpoints pass, some issues
            rand = random.random()
            if rand < 0.80:
                status = 'pass'
                finding = None
            elif rand < 0.90:
                status = 'warning'
                finding = f"Minor deviation noted in {checkpoint.title.lower()}; corrective action recommended."
            else:
                status = 'fail'
                finding = f"Non-compliance with {checkpoint.requirement_id}: {checkpoint.description}"
            
            deadline = None
            if status in ['fail', 'warning']:
                deadline = (datetime.now() + timedelta(days=30)).isoformat()
            
            assessment = ComplianceAssessment(
                checkpoint_id=checkpoint.checkpoint_id,
                checkpoint_title=checkpoint.title,
                assessment_date=datetime.now().isoformat(),
                status=status,
                finding=finding,
                corrective_action_required=status in ['fail', 'warning'],
                deadline=deadline,
                remediated=False,
            )
            assessments.append(assessment)
        
        return assessments
    
    def generate_demo_incidents(
        self,
        project_id: str,
        count: int = 5,
        days_back: int = 90,
    ) -> List[SafetyIncident]:
        """Generate synthetic safety incidents for demo.
        
        Args:
            project_id: Project identifier
            count: Number of incidents to generate
            days_back: Historical window
        
        Returns:
            List of safety incidents
        """
        incidents = []
        random.seed(hash(project_id) % (2**31))
        
        incident_types = ['near_miss', 'violation_notice', 'minor', 'major']
        severities = {'near_miss': 'minor', 'violation_notice': 'minor', 'minor': 'minor', 'major': 'major'}
        
        for i in range(count):
            days_ago = random.randint(0, days_back)
            incident_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            incident_type_key = random.choice(incident_types)
            incident_type = 'near_miss' if incident_type_key == 'near_miss' else \
                           'violation_notice' if incident_type_key == 'violation_notice' else \
                           'injury'
            
            severity = 'critical' if incident_type == 'injury' else \
                      'major' if incident_type == 'violation_notice' else \
                      'minor'
            
            incident = SafetyIncident(
                incident_id=f"{project_id}-INC-{i+1}",
                project_id=project_id,
                date=incident_date,
                incident_type=incident_type,
                severity=severity,
                location=f"Area {random.choice(['A', 'B', 'C', 'D'])}",
                involved_workers=[f"W{random.randint(1, 10):03d}"],
                root_cause="Equipment malfunction / inadequate training / procedure deviation",
                corrective_action="Inspect/repair equipment / provide refresher training / revise SOP",
                closed=random.random() > 0.3,  # 70% closed
            )
            incidents.append(incident)
        
        return incidents
    
    def calculate_safety_risk(
        self,
        project_id: str,
        incidents: List[SafetyIncident],
        assessments: List[ComplianceAssessment],
        estimated_hours_worked: float = 1000,
    ) -> SafetyRiskScore:
        """Calculate safety and compliance risk score.
        
        Args:
            project_id: Project identifier
            incidents: List of safety incidents
            assessments: List of compliance assessments
            estimated_hours_worked: Estimated worker hours (for incident rate)
        
        Returns:
            SafetyRiskScore with metrics and recommendations
        """
        # Count incidents by type
        critical_count = sum(1 for i in incidents if i.severity == 'critical')
        major_count = sum(1 for i in incidents if i.severity == 'major')
        minor_count = sum(1 for i in incidents if i.severity == 'minor')
        near_miss_count = sum(1 for i in incidents if i.incident_type == 'near_miss')
        violation_count = sum(1 for i in incidents if i.incident_type == 'violation_notice')
        
        total_incidents = len(incidents)
        
        # Incident rates (per 100K hours worked, OSHA standard)
        incident_rate = (total_incidents / max(1, estimated_hours_worked)) * 100000
        near_miss_rate = (near_miss_count / max(1, estimated_hours_worked)) * 100000
        
        # Compliance assessment
        passed = sum(1 for a in assessments if a.status == 'pass')
        failed = sum(1 for a in assessments if a.status == 'fail')
        warning = sum(1 for a in assessments if a.status == 'warning')
        total_checkpoints = len(assessments)
        compliance_score = passed / max(1, total_checkpoints)
        
        # Risk level determination
        if incident_rate > 10 or failed > 2 or critical_count > 0:
            safety_risk_level = 'high'
        elif incident_rate > 5 or failed > 0 or warning > 2:
            safety_risk_level = 'medium'
        else:
            safety_risk_level = 'low'
        
        # Regulatory risk (heuristic)
        regulatory_shutdown_probability_pct = min(100, (failed * 10 + critical_count * 25 + major_count * 5))
        
        # Audit readiness
        if compliance_score >= 0.90 and safety_risk_level == 'low':
            audit_readiness = 'good'
        elif compliance_score >= 0.70 or safety_risk_level == 'medium':
            audit_readiness = 'fair'
        else:
            audit_readiness = 'poor'
        
        # Schedule/cost impact
        rework_days = failed * 5 + critical_count * 3 + major_count * 1
        citation_cost = failed * 15000 + critical_count * 50000
        
        # Open findings
        open_findings = [
            f"{a.checkpoint_title}: {a.finding}"
            for a in assessments
            if a.status in ['fail', 'warning'] and not a.remediated
        ]
        
        # Recommended actions
        recommended_actions = []
        if safety_risk_level == 'high':
            recommended_actions.append("Immediate halt of non-compliant operations and corrective action.")
            recommended_actions.append("Increase inspection frequency and management oversight.")
        if failed > 0:
            recommended_actions.append("Execute corrective action plans for all failed checkpoints by deadline.")
        if incident_rate > 5:
            recommended_actions.append("Enhance safety training, hazard awareness, and incident reporting.")
        if warning > 2:
            recommended_actions.append("Address warning-level findings to prevent escalation.")
        
        # Summary
        summary_parts = []
        if total_incidents == 0:
            summary_parts.append("✓ No safety incidents reported")
        else:
            summary_parts.append(f"⚠️ {total_incidents} incident(s): {critical_count} critical, {major_count} major, {minor_count} minor")
        
        summary_parts.append(f"Compliance: {passed}/{total_checkpoints} checkpoints pass ({compliance_score:.0%})")
        summary_parts.append(f"Risk level: {safety_risk_level.upper()}")
        
        summary = " | ".join(summary_parts)
        
        return SafetyRiskScore(
            project_id=project_id,
            analysis_datetime=datetime.now().isoformat(),
            total_incidents=total_incidents,
            critical_incidents=critical_count,
            major_incidents=major_count,
            minor_incidents=minor_count,
            near_miss_count=near_miss_count,
            violation_notices=violation_count,
            incident_rate=incident_rate,
            near_miss_rate=near_miss_rate,
            total_checkpoints=total_checkpoints,
            passed_checkpoints=passed,
            failed_checkpoints=failed,
            warning_checkpoints=warning,
            compliance_score=compliance_score,
            safety_risk_level=safety_risk_level,
            regulatory_shutdown_probability_pct=regulatory_shutdown_probability_pct,
            audit_readiness=audit_readiness,
            estimated_rework_days=float(rework_days),
            estimated_citation_cost=float(citation_cost),
            summary=summary,
            open_findings=open_findings,
            recommended_actions=recommended_actions,
        )
    
    def project_compliance_safety(
        self,
        project_id: str,
        incidents: List[SafetyIncident],
        safety_risk_score: SafetyRiskScore,
        assessments: List[ComplianceAssessment],
    ) -> ProjectComplianceSafety:
        """Synthesize project-level compliance and safety intelligence.
        
        Args:
            project_id: Project identifier
            incidents: List of incidents
            safety_risk_score: Aggregated risk score
            assessments: List of compliance assessments
        
        Returns:
            ProjectComplianceSafety with full intelligence
        """
        # High priority findings
        high_priority = [
            a.finding
            for a in assessments
            if a.status == 'fail' and a.finding
        ]
        
        # Safety risk contribution to overall project (estimate)
        safety_risk_contribution = (
            min(100, safety_risk_score.regulatory_shutdown_probability_pct * 0.5 +
                (100 - safety_risk_score.compliance_score * 100) * 0.3)
        )
        
        # Last inspection info (demo)
        last_inspection_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Summary
        summary = f"Safety Risk: {safety_risk_score.safety_risk_level.upper()} | "
        summary += f"Compliance: {safety_risk_score.compliance_score:.0%} | "
        summary += f"Audit Readiness: {safety_risk_score.audit_readiness.upper()}"
        
        # Confidence based on data volume
        confidence = 'high' if len(incidents) + len(assessments) >= 5 else 'medium'
        
        return ProjectComplianceSafety(
            project_id=project_id,
            analysis_datetime=datetime.now().isoformat(),
            incidents=incidents,
            safety_risk_score=safety_risk_score,
            assessments=assessments,
            high_priority_findings=high_priority,
            safety_risk_contribution_pct=safety_risk_contribution,
            last_inspection_date=last_inspection_date,
            last_inspection_finding="No critical findings",
            upcoming_inspection=random.random() > 0.6,
            summary=summary,
            confidence=confidence,
        )

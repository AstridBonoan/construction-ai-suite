"""
Phase 15: Explainability & Plain-English Output

Converts raw model outputs into human-understandable explanations.
Avoids jargon, explains confidence, aligns with construction decision-making.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class Explanation:
    """Human-readable explanation of model output"""
    summary: str                    # Main finding in plain English
    confidence_level: str           # High/Medium/Low confidence
    confidence_percentage: float    # 0-100%
    key_factors: List[str]         # Why this prediction
    recommendations: List[str]     # What to do about it
    caveats: List[str]            # Limitations and assumptions


class RiskExplainer:
    """Explains risk scores in business terms"""
    
    @staticmethod
    def explain_risk_score(
        risk_score: float,
        project_name: str = "Project",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Explanation:
        """
        Explain a risk score in plain English.
        
        Args:
            risk_score: Score between 0 and 1 (0=low risk, 1=high risk)
            project_name: Name of the project
            additional_context: Dict with 'budget', 'duration', 'complexity', etc.
        
        Returns:
            Explanation object with human-readable content
        """
        
        # Determine risk level and confidence
        if risk_score < 0.3:
            risk_level = "Low Risk"
            confidence = 0.85
            interpretation = "this project is unlikely to face delays"
            action_level = "Monitor routine"
        elif risk_score < 0.6:
            risk_level = "Medium Risk"
            confidence = 0.75
            interpretation = "this project has some risk of delays"
            action_level = "Plan contingencies"
        else:
            risk_level = "High Risk"
            confidence = 0.80
            interpretation = "this project is at significant risk of delays"
            action_level = "Implement safeguards now"
        
        # Build summary
        summary = (
            f"{project_name}: {risk_level} ({risk_score:.0%} likelihood). "
            f"Based on historical patterns, {interpretation}. "
            f"{action_level}."
        )
        
        # Key factors (would come from SHAP or similar in production)
        factors = [
            "Similar past projects experienced delays",
            "Project complexity is above average for this type",
            "Resource allocation patterns match at-risk projects"
        ]

        # If callers provide breakdown/features, produce attributed short statements
        if additional_context and isinstance(additional_context, dict):
            bd = additional_context.get("breakdown")
            feats = additional_context.get("features") or {}
            if bd and isinstance(bd, list):
                # top contributors
                top = bd[:3]
                factors = [f"{t['factor']}: +{t.get('contribution', 0.0):.2f}" for t in top]
                # workforce attribution
                for t in bd:
                    if t.get("factor") == "workforce_unreliability_score":
                        c = t.get("contribution", 0.0)
                        factors.insert(0, f"Labor unreliability contributed +{c*100:.1f} percentage points to overall risk")
                    if t.get("factor") == "workforce_pattern_penalty":
                        c = t.get("contribution", 0.0)
                        factors.insert(0, f"Repeat no-shows patterns added +{c*100:.1f} percentage points risk")
                    if t.get("factor") == "iot_amplification":
                        c = t.get("contribution", 0.0)
                        factors.append(f"Adverse site conditions amplified baseline risk by {c*100:.1f} percentage points")
                    if t.get("factor") == "safety_incident_probability":
                        c = t.get("contribution", 0.0)
                        factors.append(f"Safety incident probability contributed +{c*100:.1f} percentage points to risk")
                    if t.get("factor") == "compliance_exposure_score":
                        c = t.get("contribution", 0.0)
                        factors.append(f"Compliance exposure added +{c*100:.1f} percentage points to risk")
        
        # Recommendations
        if risk_score < 0.3:
            recommendations = [
                "Proceed with standard planning",
                "Schedule monthly progress reviews",
                "Track actual vs. planned metrics"
            ]
        elif risk_score < 0.6:
            recommendations = [
                "Add 10-15% time buffer to schedule",
                "Assign dedicated project manager",
                "Plan weekly risk reviews",
                "Identify key dependencies early"
            ]
        else:
            recommendations = [
                "Add 20-30% time buffer to schedule",
                "Consider reducing scope or timeline",
                "Allocate senior leadership oversight",
                "Implement daily risk standups",
                "Have backup suppliers/contractors on standby"
            ]
        
        # Caveats
        caveats = [
            "Predictions based on historical project data",
            "Cannot predict external factors (weather, supply chain disruptions)",
            "Actual performance depends on execution and management",
            "Model assumes similar resource availability as historical projects"
        ]
        
        return Explanation(
            summary=summary,
            confidence_level=f"{'High' if confidence > 0.8 else 'Medium' if confidence > 0.65 else 'Low'} Confidence",
            confidence_percentage=confidence * 100,
            key_factors=factors,
            recommendations=recommendations,
            caveats=caveats
        )


class DelayExplainer:
    """Explains predicted delay in business terms"""
    
    @staticmethod
    def explain_delay_prediction(
        delay_days: float,
        delay_probability: float,
        project_name: str = "Project"
    ) -> Explanation:
        """
        Explain predicted delay in plain English.
        
        Args:
            delay_days: Predicted delay in days
            delay_probability: Probability of delay (0-1)
            project_name: Name of project
        
        Returns:
            Explanation object
        """
        
        # Determine confidence level
        confidence = delay_probability if delay_probability > 0.5 else (1 - delay_probability)
        
        if delay_probability < 0.3:
            outcome = "is unlikely to be delayed"
            confidence_label = "Low probability"
        elif delay_probability < 0.7:
            outcome = f"may be delayed by {int(delay_days)} days"
            confidence_label = "Moderate probability"
        else:
            outcome = f"is likely to be delayed by {int(delay_days)} days"
            confidence_label = "High probability"
        
        summary = (
            f"{project_name}: {outcome}. "
            f"Based on project characteristics, there's a {delay_probability:.0%} chance of delays. "
            f"If delays occur, we estimate {int(delay_days)} days impact."
        )
        
        # Recommendations based on delay expectation
        if delay_probability < 0.3:
            recommendations = [
                "Follow standard project timeline",
                "Standard risk management sufficient"
            ]
        elif delay_probability < 0.7:
            recommendations = [
                f"Plan for potential {int(delay_days*0.5)}-{int(delay_days)} day delay",
                "Identify activities that can be parallelized",
                "Establish clear decision criteria for schedule adjustments",
                "Brief stakeholders on delay possibility"
            ]
        else:
            recommendations = [
                f"Budget for {int(delay_days)} days of delay in timeline",
                "Identify and mitigate schedule risks immediately",
                "Increase project visibility and reporting",
                "Prepare communication plan for potential delays",
                "Consider phased delivery to reduce end-date risk"
            ]
        
        key_factors = [
            "Project scope and complexity indicators",
            "Historical patterns for similar project types",
            "Resource availability and allocation patterns",
            "Schedule buffer currently built in"
        ]
        
        caveats = [
            "Prediction is probabilistic, not deterministic",
            "Actual delays depend on execution, resources, and external factors",
            "Model cannot predict one-time events (major incidents, natural disasters)",
            "Delay prediction is most accurate 3-6 months before completion"
        ]
        
        return Explanation(
            summary=summary,
            confidence_level=confidence_label,
            confidence_percentage=confidence * 100,
            key_factors=key_factors,
            recommendations=recommendations,
            caveats=caveats
        )


class AnomalyExplainer:
    """Explains detected anomalies"""
    
    @staticmethod
    def explain_anomaly(
        anomaly_type: str,
        severity: float,
        project_name: str = "Project",
        details: Optional[Dict[str, Any]] = None
    ) -> Explanation:
        """
        Explain detected anomaly in plain English.
        
        Args:
            anomaly_type: 'budget_variance', 'schedule_slip', 'resource_utilization', etc.
            severity: 0-1, where 1 is critical
            project_name: Project name
            details: Additional context
        
        Returns:
            Explanation object
        """
        
        type_descriptions = {
            'budget_variance': 'Budget variance detected',
            'schedule_slip': 'Schedule slipping',
            'resource_utilization': 'Resource utilization issue',
            'scope_creep': 'Scope expansion detected',
            'quality_issue': 'Quality metric deviation',
            'milestone_miss': 'Milestone not tracking to plan'
        }
        
        description = type_descriptions.get(anomaly_type, 'Anomaly detected')
        
        # Determine action needed
        if severity < 0.4:
            severity_label = "Minor"
            action = "Monitor and document"
        elif severity < 0.7:
            severity_label = "Moderate"
            action = "Review with project lead"
        else:
            severity_label = "Significant"
            action = "Escalate immediately"
        
        summary = (
            f"{project_name}: {severity_label} {description}. "
            f"This requires attention. {action} to understand root cause and plan response."
        )
        
        recommendations = [
            f"Schedule review meeting with stakeholders",
            "Investigate root cause of anomaly",
            "Assess impact on schedule, budget, and quality",
            "Develop corrective action plan"
        ]
        
        key_factors = [
            f"Current metrics deviate from baseline",
            "Trend suggests potential larger issue",
            "Similar patterns preceded problems in past projects"
        ]
        
        caveats = [
            "Anomaly detection is based on statistical patterns",
            "Not all anomalies indicate problems (some may be due to data quality)",
            "Context matters - what looks anomalous may be expected given circumstances"
        ]
        
        return Explanation(
            summary=summary,
            confidence_level="Medium Confidence",
            confidence_percentage=0.75 * (1 - (severity/2)),
            key_factors=key_factors,
            recommendations=recommendations,
            caveats=caveats
        )


def format_explanation_for_api(explanation: Explanation) -> Dict[str, Any]:
    """Convert Explanation dataclass to API response format"""
    return {
        'summary': explanation.summary,
        'confidence': {
            'level': explanation.confidence_level,
            'percentage': f"{explanation.confidence_percentage:.0f}%"
        },
        'key_factors': explanation.key_factors,
        'recommendations': explanation.recommendations,
        'caveats': explanation.caveats,
        'note': (
            'This explanation uses plain language and business context. '
            'All recommendations should be evaluated by project management before implementation.'
        )
    }


def format_explanation_for_display(explanation: Explanation) -> str:
    """Format explanation as readable text for UI/reports"""
    
    text = []
    text.append("=" * 70)
    text.append("PROJECT RISK ASSESSMENT")
    text.append("=" * 70)
    text.append("")
    
    text.append("SUMMARY:")
    text.append(f"  {explanation.summary}")
    text.append("")
    
    text.append(f"CONFIDENCE: {explanation.confidence_level} ({explanation.confidence_percentage:.0f}%)")
    text.append("")
    
    text.append("KEY FACTORS:")
    for i, factor in enumerate(explanation.key_factors, 1):
        text.append(f"  {i}. {factor}")
    text.append("")
    
    text.append("RECOMMENDATIONS:")
    for i, rec in enumerate(explanation.recommendations, 1):
        text.append(f"  {i}. {rec}")
    text.append("")
    
    text.append("IMPORTANT CAVEATS:")
    for i, caveat in enumerate(explanation.caveats, 1):
        text.append(f"  • {caveat}")
    text.append("")
    
    text.append("=" * 70)
    
    return "\n".join(text)

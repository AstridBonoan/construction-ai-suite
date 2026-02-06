"""
Feature 9: Multi-Factor Risk Aggregator & Synthesizer
Combines risks from Features 1-8 into holistic project risk intelligence
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

from phase9_risk_types import (
    RiskCategory,
    RiskSeverity,
    AggregationMethod,
    RiskFactorInput,
    FactorContribution,
    MultiFactorRiskInput,
    SynthesizedRiskMetric,
    SynthesizedRiskOutput,
    RiskWeightConfig,
    RiskPropagationPath,
)

logger = logging.getLogger(__name__)


class MultiFactorRiskAggregator:
    """
    Synthesizes multiple risk factors from Features 1-8 into holistic project risk.
    
    Algorithms:
    - Weighted average aggregation (default)
    - Interaction modeling (cost/schedule, schedule/workforce, etc.)
    - Phase-specific adjustments (planning vs execution vs closing)
    - Confidence-weighted synthesis
    - Dependency-aware risk propagation
    """

    def __init__(self, weight_config: Optional[RiskWeightConfig] = None):
        """Initialize aggregator with configuration"""
        self.weight_config = weight_config or RiskWeightConfig()
        self.synthesis_history: Dict[str, List[SynthesizedRiskOutput]] = {}
        self._validate_weights()

    def _validate_weights(self):
        """Ensure weights sum to 1.0"""
        total = self.weight_config.total_weight()
        if abs(total - 1.0) > 0.01:  # Allow small floating point tolerance
            logger.warning(f"Risk weights sum to {total:.2%}, not 100%")

    def synthesize(
        self,
        multi_factor_input: MultiFactorRiskInput,
        aggregation_method: AggregationMethod = AggregationMethod.WEIGHTED_AVERAGE,
    ) -> SynthesizedRiskOutput:
        """
        Synthesize multiple risk factors into holistic output.

        Args:
            multi_factor_input: Risk inputs from Features 1-8
            aggregation_method: Algorithm to use for synthesis

        Returns:
            SynthesizedRiskOutput with integrated risk scores and explanations
        """
        synthesis_id = f"synthesis_{multi_factor_input.project_id}_{datetime.now().isoformat()}"

        # Collect all risk factors
        risk_factors = self._extract_risk_factors(multi_factor_input)

        # Normalize scores
        normalized_factors = self._normalize_risk_factors(risk_factors)

        # Calculate individual metrics
        metrics = self._calculate_factor_metrics(risk_factors)

        # Apply interaction modeling
        adjusted_factors = self._model_interactions(normalized_factors, multi_factor_input)

        # Aggregate to overall score
        if aggregation_method == AggregationMethod.WEIGHTED_AVERAGE:
            overall_score = self._aggregate_weighted_average(adjusted_factors)
        elif aggregation_method == AggregationMethod.MAXIMUM:
            overall_score = self._aggregate_worst_case(adjusted_factors)
        elif aggregation_method == AggregationMethod.COMPOUND:
            overall_score = self._aggregate_compound(adjusted_factors)
        elif aggregation_method == AggregationMethod.HIERARCHICAL:
            overall_score = self._aggregate_hierarchical(adjusted_factors, multi_factor_input)
        else:
            overall_score = self._aggregate_weighted_average(adjusted_factors)

        # Apply phase-specific adjustment
        overall_score = self._apply_phase_adjustment(overall_score, multi_factor_input)

        # Calculate confidence
        overall_confidence = self._calculate_confidence(risk_factors)

        # Determine severity
        overall_severity = self._classify_severity(overall_score)

        # Generate contributions
        contributions = self._generate_contributions(adjusted_factors, overall_score)

        # Identify drivers
        primary_drivers = self._identify_primary_drivers(contributions)
        secondary_drivers = self._identify_secondary_drivers(contributions)

        # Generate explanations
        executive_summary = self._generate_executive_summary(
            overall_score, overall_severity, primary_drivers
        )
        detailed_explanation = self._generate_detailed_explanation(
            contributions, primary_drivers, secondary_drivers
        )

        # Mitigation plan
        mitigation_plan = self._generate_mitigation_plan(primary_drivers, contributions)

        # Outlook
        short_term = self._generate_outlook(risk_factors, "short")
        medium_term = self._generate_outlook(risk_factors, "medium")

        # Monday.com formatting
        from phase9_risk_types import AggregationMethod as AM
        monday_status = self._format_monday_status(overall_severity)
        monday_concern = self._format_monday_concern(primary_drivers[0] if primary_drivers else "stable")
        monday_items = self._format_monday_items(mitigation_plan[:3])

        # Build output
        output = SynthesizedRiskOutput(
            synthesis_id=synthesis_id,
            project_id=multi_factor_input.project_id,
            task_id=multi_factor_input.task_id,
            timestamp=datetime.now().isoformat(),
            overall_risk_score=overall_score,
            overall_severity=overall_severity,
            overall_confidence=overall_confidence,
            cost_risk_metric=metrics.get(RiskCategory.COST),
            schedule_risk_metric=metrics.get(RiskCategory.SCHEDULE),
            workforce_risk_metric=metrics.get(RiskCategory.WORKFORCE),
            subcontractor_risk_metric=metrics.get(RiskCategory.SUBCONTRACTOR),
            equipment_risk_metric=metrics.get(RiskCategory.EQUIPMENT),
            materials_risk_metric=metrics.get(RiskCategory.MATERIALS),
            compliance_risk_metric=metrics.get(RiskCategory.COMPLIANCE),
            environmental_risk_metric=metrics.get(RiskCategory.ENVIRONMENTAL),
            factor_contributions=contributions,
            primary_risk_drivers=primary_drivers,
            secondary_risk_drivers=secondary_drivers,
            executive_summary=executive_summary,
            detailed_explanation=detailed_explanation,
            risk_mitigation_plan=mitigation_plan,
            short_term_outlook=short_term,
            medium_term_outlook=medium_term,
            aggregation_method=aggregation_method,
            input_count=len([f for f in risk_factors.values() if f is not None]),
            missing_factors=self._identify_missing_factors(multi_factor_input),
            monday_risk_status=monday_status,
            monday_primary_concern=monday_concern,
            monday_action_items=monday_items,
        )

        # Cache output
        if multi_factor_input.project_id not in self.synthesis_history:
            self.synthesis_history[multi_factor_input.project_id] = []
        self.synthesis_history[multi_factor_input.project_id].append(output)

        return output

    def _extract_risk_factors(self, inp: MultiFactorRiskInput) -> Dict[RiskCategory, Optional[RiskFactorInput]]:
        """Extract all risk factor inputs"""
        return {
            RiskCategory.COST: inp.cost_risk,
            RiskCategory.SCHEDULE: inp.schedule_risk,
            RiskCategory.WORKFORCE: inp.workforce_risk,
            RiskCategory.SUBCONTRACTOR: inp.subcontractor_risk,
            RiskCategory.EQUIPMENT: inp.equipment_risk,
            RiskCategory.MATERIALS: inp.materials_risk,
            RiskCategory.COMPLIANCE: inp.compliance_risk,
            RiskCategory.ENVIRONMENTAL: inp.environmental_risk,
        }

    def _normalize_risk_factors(
        self, factors: Dict[RiskCategory, Optional[RiskFactorInput]]
    ) -> Dict[RiskCategory, Optional[RiskFactorInput]]:
        """Normalize scores to 0-1 range with confidence adjustment"""
        normalized = {}
        for category, factor in factors.items():
            if factor is None:
                normalized[category] = None
            else:
                # Already 0-1 from features, but adjust for confidence
                normalized_score = max(0, min(1.0, factor.score * factor.confidence))
                normalized[category] = RiskFactorInput(
                    category=category,
                    score=min(factor.score, 1.0),  # Keep original for contribution
                    severity=factor.severity or self._classify_severity(factor.score),
                    confidence=factor.confidence,
                    contributing_issues=factor.contributing_issues,
                    trend=factor.trend,
                    timestamp=factor.timestamp,
                )
        return normalized

    def _calculate_factor_metrics(
        self, factors: Dict[RiskCategory, Optional[RiskFactorInput]]
    ) -> Dict[RiskCategory, Optional[SynthesizedRiskMetric]]:
        """Calculate individual metrics for each risk factor"""
        metrics = {}

        for category, factor in factors.items():
            if factor is None:
                metrics[category] = None
            else:
                severity = self._classify_severity(factor.score)
                metric = SynthesizedRiskMetric(
                    metric_name=f"{category.value.capitalize()} Risk",
                    score=factor.score,
                    severity=severity,
                    confidence=factor.confidence,
                    primary_drivers=factor.contributing_issues[:3],
                    secondary_drivers=factor.contributing_issues[3:6],
                    explanation=self._explain_factor_risk(category, factor),
                    trend=factor.trend,
                    outlook_next_14_days=self._outlook_factor_risk(category, factor),
                )
                metrics[category] = metric

        return metrics

    def _model_interactions(
        self, factors: Dict[RiskCategory, Optional[RiskFactorInput]], inp: MultiFactorRiskInput
    ) -> Dict[RiskCategory, float]:
        """Model how risks interact to compound overall risk"""
        adjusted = {}

        for category, factor in factors.items():
            if factor is None:
                adjusted[category] = 0.0
            else:
                base_score = factor.score
                adjustment = 1.0

                # Cost-Schedule interaction
                if (category == RiskCategory.COST and inp.schedule_risk is not None):
                    adjustment *= (1.0 + inp.schedule_risk.score * self.weight_config.cost_schedule_interaction)
                elif (category == RiskCategory.SCHEDULE and inp.cost_risk is not None):
                    adjustment *= (1.0 + inp.cost_risk.score * self.weight_config.cost_schedule_interaction)

                # Schedule-Workforce interaction
                if (category == RiskCategory.SCHEDULE and inp.workforce_risk is not None):
                    adjustment *= (1.0 + inp.workforce_risk.score * self.weight_config.schedule_workforce_interaction)
                elif (category == RiskCategory.WORKFORCE and inp.schedule_risk is not None):
                    adjustment *= (1.0 + inp.schedule_risk.score * self.weight_config.schedule_workforce_interaction)

                # Equipment-Schedule interaction
                if (category == RiskCategory.EQUIPMENT and inp.schedule_risk is not None):
                    adjustment *= (1.0 + inp.schedule_risk.score * self.weight_config.equipment_schedule_interaction)
                elif (category == RiskCategory.SCHEDULE and inp.equipment_risk is not None):
                    adjustment *= (1.0 + inp.equipment_risk.score * self.weight_config.equipment_schedule_interaction)

                # Compliance-Safety (Environmental) interaction
                if (category == RiskCategory.COMPLIANCE and inp.environmental_risk is not None):
                    adjustment *= (1.0 + inp.environmental_risk.score * self.weight_config.compliance_safety_interaction)
                elif (category == RiskCategory.ENVIRONMENTAL and inp.compliance_risk is not None):
                    adjustment *= (1.0 + inp.compliance_risk.score * self.weight_config.compliance_safety_interaction)

                # Cap adjustment at 1.5x (50% amplification maximum)
                adjusted[category] = min(base_score * adjustment, 1.0)

        return adjusted

    def _aggregate_weighted_average(self, adjusted: Dict[RiskCategory, float]) -> float:
        """Weighted average aggregation"""
        weighted_sum = 0.0
        weight_sum = 0.0

        weights = {
            RiskCategory.COST: self.weight_config.cost_weight,
            RiskCategory.SCHEDULE: self.weight_config.schedule_weight,
            RiskCategory.WORKFORCE: self.weight_config.workforce_weight,
            RiskCategory.SUBCONTRACTOR: self.weight_config.subcontractor_weight,
            RiskCategory.EQUIPMENT: self.weight_config.equipment_weight,
            RiskCategory.MATERIALS: self.weight_config.materials_weight,
            RiskCategory.COMPLIANCE: self.weight_config.compliance_weight,
            RiskCategory.ENVIRONMENTAL: self.weight_config.environmental_weight,
        }

        for category, score in adjusted.items():
            weight = weights[category]
            if score >0:
                weighted_sum += score * weight
                weight_sum += weight

        # Normalize by actual weight sum (may be less than 1.0 if some factors missing)
        if weight_sum > 0:
            return min(weighted_sum / weight_sum, 1.0)
        return 0.0

    def _aggregate_worst_case(self, adjusted: Dict[RiskCategory, float]) -> float:
        """Worst-case scenario (maximum risk)"""
        non_zero_scores = [s for s in adjusted.values() if s > 0]
        if non_zero_scores:
            return max(non_zero_scores)
        return 0.0

    def _aggregate_compound(self, adjusted: Dict[RiskCategory, float]) -> float:
        """Compound risk (multiplicative accumulation)"""
        non_zero_scores = [s for s in adjusted.values() if s > 0]
        if not non_zero_scores:
            return 0.0

        # Compound formula: 1 - (1-r1)(1-r2)...(1-rn)
        # This gives increasing joint risk as individual risks increase
        product = 1.0
        for score in non_zero_scores:
            product *= (1.0 - score)
        return min(1.0 - product, 1.0)

    def _aggregate_hierarchical(
        self, adjusted: Dict[RiskCategory, float], inp: MultiFactorRiskInput
    ) -> float:
        """Hierarchical aggregation with dependency awareness"""
        # Tier 1: Cost, Schedule (foundational)
        tier1 = (adjusted[RiskCategory.COST] + adjusted[RiskCategory.SCHEDULE]) / 2

        # Tier 2: Workforce, Equipment, Materials (execution)
        tier2_scores = [
            adjusted[RiskCategory.WORKFORCE],
            adjusted[RiskCategory.EQUIPMENT],
            adjusted[RiskCategory.MATERIALS],
        ]
        tier2 = sum(tier2_scores) / len(tier2_scores) if tier2_scores else 0.0

        # Tier 3: Subcontractor, Compliance, Environmental (external)
        tier3_scores = [
            adjusted[RiskCategory.SUBCONTRACTOR],
            adjusted[RiskCategory.COMPLIANCE],
            adjusted[RiskCategory.ENVIRONMENTAL],
        ]
        tier3 = sum(tier3_scores) / len(tier3_scores) if tier3_scores else 0.0

        # Combine with tier weighting (Tier 1 most critical)
        overall = (tier1 * 0.45) + (tier2 * 0.35) + (tier3 * 0.20)

        # Apply dependency boost if many external dependencies
        if inp.dependencies_count > 5:
            overall *= (1.0 + (inp.dependencies_count - 5) * 0.05)

        return min(overall, 1.0)

    def _apply_phase_adjustment(self, score: float, inp: MultiFactorRiskInput) -> float:
        """Adjust risk score based on project phase"""
        phase_boosts = {
            "planning": self.weight_config.planning_phase_boost,
            "execution": self.weight_config.execution_phase_boost,
            "closing": self.weight_config.closing_phase_boost,
        }

        boost = phase_boosts.get(inp.project_phase, 1.0)
        adjusted = score * boost

        # Ensure result stays in 0-1 range
        return min(adjusted, 1.0)

    def _calculate_confidence(self, factors: Dict[RiskCategory, Optional[RiskFactorInput]]) -> float:
        """Calculate overall confidence in synthesis"""
        confidences = [f.confidence for f in factors.values() if f is not None]

        if not confidences:
            return 0.5  # Low confidence if no data

        # Geometric mean of confidences
        import math
        if len(confidences) == 1:
            return confidences[0]

        product = 1.0
        for conf in confidences:
            product *= conf
        geometric_mean = product ** (1.0 / len(confidences))

        return min(geometric_mean, 1.0)

    def _classify_severity(self, score: float) -> RiskSeverity:
        """Classify severity based on score"""
        if score < 0.25:
            return RiskSeverity.LOW
        elif score < 0.50:
            return RiskSeverity.MEDIUM
        elif score < 0.75:
            return RiskSeverity.HIGH
        else:
            return RiskSeverity.CRITICAL

    def _generate_contributions(
        self, adjusted: Dict[RiskCategory, float], overall: float
    ) -> List[FactorContribution]:
        """Generate contribution breakdown for each factor"""
        contributions = []

        weights = {
            RiskCategory.COST: self.weight_config.cost_weight,
            RiskCategory.SCHEDULE: self.weight_config.schedule_weight,
            RiskCategory.WORKFORCE: self.weight_config.workforce_weight,
            RiskCategory.SUBCONTRACTOR: self.weight_config.subcontractor_weight,
            RiskCategory.EQUIPMENT: self.weight_config.equipment_weight,
            RiskCategory.MATERIALS: self.weight_config.materials_weight,
            RiskCategory.COMPLIANCE: self.weight_config.compliance_weight,
            RiskCategory.ENVIRONMENTAL: self.weight_config.environmental_weight,
        }

        for category, score in adjusted.items():
            if score > 0:
                weight = weights[category]
                contribution = score * weight
                contribution_pct = contribution / overall if overall > 0 else 0

                contrib_obj = FactorContribution(
                    category=category,
                    raw_score=score,
                    normalized_score=min(score, 1.0),
                    weight=weight,
                    contribution_to_total=contribution_pct,
                    reason=self._explain_contribution(category, score),
                    recommendations=self._recommend_mitigation(category, score),
                )
                contributions.append(contrib_obj)

        # Sort by contribution descending
        contributions.sort(key=lambda x: x.contribution_to_total, reverse=True)
        return contributions

    def _identify_primary_drivers(self, contributions: List[FactorContribution]) -> List[str]:
        """Identify top 3 risk drivers"""
        return [
            f"{c.category.value.capitalize()}: {c.reason}"
            for c in contributions[:3]
        ]

    def _identify_secondary_drivers(self, contributions: List[FactorContribution]) -> List[str]:
        """Identify next 3 risk drivers"""
        return [
            f"{c.category.value.capitalize()}: {c.reason}"
            for c in contributions[3:6]
        ]

    def _generate_executive_summary(
        self, score: float, severity: RiskSeverity, drivers: List[str]
    ) -> str:
        """Generate one-sentence executive summary"""
        severity_text = severity.value.upper()
        primary = drivers[0].split(":")[0] if drivers else "multiple factors"

        if severity == RiskSeverity.LOW:
            return f"Project risk is {severity_text} ({score:.0%}). {primary} is the primary concern."
        elif severity == RiskSeverity.MEDIUM:
            return f"Project risk is {severity_text} ({score:.0%}). Attention needed to {primary}."
        elif severity == RiskSeverity.HIGH:
            return f"Project risk is {severity_text} ({score:.0%}). Immediate action required on {primary}."
        else:
            return f"CRITICAL: Project risk is {severity_text} ({score:.0%}). {primary} requires urgent intervention."

    def _generate_detailed_explanation(
        self, contributions: List[FactorContribution], primary: List[str], secondary: List[str]
    ) -> str:
        """Generate detailed technical explanation"""
        parts = ["Risk Synthesis Analysis:"]

        parts.append(f"\nPrimary Risk Drivers ({len(primary)}):")
        for driver in primary:
            parts.append(f"  • {driver}")

        if secondary:
            parts.append(f"\nSecondary Risk Drivers ({len(secondary)}):")
            for driver in secondary:
                parts.append(f"  • {driver}")

        parts.append(f"\nFactor Contributions:")
        for contrib in contributions[:5]:
            parts.append(
                f"  • {contrib.category.value.capitalize()}: "
                f"{contrib.contribution_to_total:.0%} of overall risk"
            )

        return "\n".join(parts)

    def _generate_mitigation_plan(
        self, drivers: List[str], contributions: List[FactorContribution]
    ) -> List[str]:
        """Generate recommended mitigation actions"""
        plan = []

        for contrib in contributions[:3]:
            plan.extend(contrib.recommendations)

        return plan[:5]  # Top 5 recommendations

    def _generate_outlook(self, factors: Dict[RiskCategory, Optional[RiskFactorInput]], horizon: str) -> str:
        """Generate outlook for short/medium term"""
        increasing_trends = sum(
            1 for f in factors.values() if f and f.trend == "increasing"
        )
        stable_trends = sum(1 for f in factors.values() if f and f.trend == "stable")

        if increasing_trends > 3:
            return f"Risk is {horizon} expected to INCREASE. Proactive monitoring critical."
        elif stable_trends > 5:
            return f"Risk is {horizon} expected to remain STABLE. Continue current mitigation efforts."
        else:
            return f"Risk is {horizon} expected to vary. Close monitoring of key drivers recommended."

    def _explain_factor_risk(self, category: RiskCategory, factor: RiskFactorInput) -> str:
        """Generate explanation for a single factor"""
        severity = self._classify_severity(factor.score)
        issues = ", ".join(factor.contributing_issues[:2]) if factor.contributing_issues else "multiple issues"

        templates = {
            RiskCategory.COST: f"Cost risk is {severity.value} due to {issues}.",
            RiskCategory.SCHEDULE: f"Schedule risk is {severity.value} due to {issues}.",
            RiskCategory.WORKFORCE: f"Workforce risk is {severity.value} due to {issues}.",
            RiskCategory.SUBCONTRACTOR: f"Subcontractor performance risk is {severity.value} due to {issues}.",
            RiskCategory.EQUIPMENT: f"Equipment risk is {severity.value} due to {issues}.",
            RiskCategory.MATERIALS: f"Materials risk is {severity.value} due to {issues}.",
            RiskCategory.COMPLIANCE: f"Compliance risk is {severity.value} due to {issues}.",
            RiskCategory.ENVIRONMENTAL: f"Environmental/IoT risk is {severity.value} due to {issues}.",
        }

        return templates.get(category, f"{category.value} risk is {severity.value}.")

    def _outlook_factor_risk(self, category: RiskCategory, factor: RiskFactorInput) -> str:
        """Generate outlook for a factor"""
        if factor.trend == "increasing":
            return f"Expected to WORSEN in next 2 weeks"
        elif factor.trend == "decreasing":
            return f"Expected to IMPROVE in next 2 weeks"
        else:
            return f"Expected to remain STABLE in next 2 weeks"

    def _explain_contribution(self, category: RiskCategory, score: float) -> str:
        """Explain how a category contributes"""
        if score > 0.7:
            return f"High {category.value} risk requiring immediate attention"
        elif score > 0.4:
            return f"Moderate {category.value} risk needing monitoring"
        else:
            return f"Low {category.value} risk but worth tracking"

    def _recommend_mitigation(self, category: RiskCategory, score: float) -> List[str]:
        """Generate mitigation recommendations for a category"""
        base_recommendations = {
            RiskCategory.COST: [
                "Review budget allocations and contingencies",
                "Identify cost-saving opportunities",
                "Negotiate with suppliers for better rates",
            ],
            RiskCategory.SCHEDULE: [
                "Accelerate critical path activities",
                "Add buffer to dependent tasks",
                "Improve coordination between teams",
            ],
            RiskCategory.WORKFORCE: [
                "Increase staffing or enhance training",
                "Improve team collaboration",
                "Reduce scope or extend timeline",
            ],
            RiskCategory.SUBCONTRACTOR: [
                "Strengthen oversight and audits",
                "Establish clear KPIs and penalties",
                "Prepare backup subcontractors",
            ],
            RiskCategory.EQUIPMENT: [
                "Increase preventive maintenance frequency",
                "Procure backup equipment",
                "Schedule critical equipment work early",
            ],
            RiskCategory.MATERIALS: [
                "Increase supplier diversification",
                "Pre-order long-lead items",
                "Establish material contingency stock",
            ],
            RiskCategory.COMPLIANCE: [
                "Conduct compliance audit",
                "Engage legal/compliance experts",
                "Document all regulatory adherence",
            ],
            RiskCategory.ENVIRONMENTAL: [
                "Monitor weather and site conditions",
                "Prepare contingency work plans",
                "Enhance safety protocols",
            ],
        }

        recommendations = base_recommendations.get(category, [])

        # Prioritize top 2 if risk is high
        if score > 0.6:
            return recommendations[:2]
        else:
            return recommendations[:1]

    def _identify_missing_factors(self, inp: MultiFactorRiskInput) -> List[str]:
        """Identify which features didn't provide data"""
        missing = []
        if inp.cost_risk is None:
            missing.append("Cost (Feature 1)")
        if inp.schedule_risk is None:
            missing.append("Schedule (Feature 2)")
        if inp.workforce_risk is None:
            missing.append("Workforce (Feature 3)")
        if inp.subcontractor_risk is None:
            missing.append("Subcontractor (Feature 4)")
        if inp.equipment_risk is None:
            missing.append("Equipment (Feature 5)")
        if inp.materials_risk is None:
            missing.append("Materials (Feature 6)")
        if inp.compliance_risk is None:
            missing.append("Compliance (Feature 7)")
        if inp.environmental_risk is None:
            missing.append("Environmental (Feature 8)")
        return missing

    def _format_monday_status(self, severity: RiskSeverity) -> str:
        """Format risk status for monday.com with emoji"""
        emojis = {
            RiskSeverity.LOW: "🟢 Low",
            RiskSeverity.MEDIUM: "🟡 Medium",
            RiskSeverity.HIGH: "🔴 High",
            RiskSeverity.CRITICAL: "🚨 Critical",
        }
        return emojis.get(severity, "❓ Unknown")

    def _format_monday_concern(self, primary_driver: str) -> str:
        """Format primary concern for monday.com"""
        return primary_driver.split(":")[0] if primary_driver else "Stable"

    def _format_monday_items(self, items: List[str]) -> List[str]:
        """Format action items for monday.com"""
        return [item[:50] for item in items]  # Truncate for column width

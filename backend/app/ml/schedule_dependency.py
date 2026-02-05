"""
Schedule dependency graph, critical path analysis, and delay propagation.

Designed for deterministic, testable behavior and easy integration with
the Core AI risk engine (Feature 1).

Key classes:
- Task: represents a single task/node
- DependencyGraph: holds tasks and dependencies and computes scheduling

This module has no external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class DependencyType(str, Enum):
    FINISH_TO_START = "FS"
    START_TO_START = "SS"
    FINISH_TO_FINISH = "FF"


@dataclass
class Task:
    id: str
    name: str
    duration_days: int
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    resource: Optional[str] = None
    monday_id: Optional[str] = None

    # Computed scheduling fields
    es: Optional[int] = None  # earliest start (days from project start)
    ef: Optional[int] = None  # earliest finish
    ls: Optional[int] = None  # latest start
    lf: Optional[int] = None  # latest finish
    float: Optional[int] = None

    def __post_init__(self):
        if self.duration_days < 0:
            raise ValueError("duration_days must be non-negative")


@dataclass
class Dependency:
    predecessor: str
    successor: str
    type: DependencyType = DependencyType.FINISH_TO_START
    lag: int = 0  # lag in days (can be negative)


class DependencyGraph:
    """Directed acyclic graph for tasks and dependencies.

    Notes:
    - Uses integer day units for determinism and testability.
    - All time calculations are relative (days from project start).
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.adj: Dict[str, List[Dependency]] = {}
        self.rev_adj: Dict[str, List[Dependency]] = {}

    def add_task(self, task: Task) -> None:
        if task.id in self.tasks:
            raise ValueError(f"Task {task.id} already exists")
        self.tasks[task.id] = task
        self.adj[task.id] = []
        self.rev_adj[task.id] = []

    def add_dependency(self, dependency: Dependency) -> None:
        if dependency.predecessor not in self.tasks:
            raise KeyError(f"Predecessor {dependency.predecessor} not found")
        if dependency.successor not in self.tasks:
            raise KeyError(f"Successor {dependency.successor} not found")
        self.adj[dependency.predecessor].append(dependency)
        self.rev_adj[dependency.successor].append(dependency)

    def topological_sort(self) -> List[str]:
        # Kahn's algorithm
        in_degree = {tid: 0 for tid in self.tasks}
        for deps in self.adj.values():
            for d in deps:
                in_degree[d.successor] += 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order: List[str] = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for dep in self.adj.get(n, []):
                in_degree[dep.successor] -= 1
                if in_degree[dep.successor] == 0:
                    queue.append(dep.successor)

        if len(order) != len(self.tasks):
            raise ValueError("Graph has cycles or disconnected components")
        return order

    def compute_earliest_times(self) -> None:
        """Compute earliest start/finish (ES/EF) in days from project start."""
        order = self.topological_sort()
        for tid in order:
            task = self.tasks[tid]
            # Base ES
            es = 0
            # Consider all predecessors
            for dep in self.rev_adj.get(tid, []):
                pred = self.tasks[dep.predecessor]
                if pred.ef is None:
                    raise RuntimeError("Predecessor EF not computed")
                if dep.type == DependencyType.FINISH_TO_START:
                    candidate = pred.ef + dep.lag
                elif dep.type == DependencyType.START_TO_START:
                    candidate = pred.es + dep.lag
                elif dep.type == DependencyType.FINISH_TO_FINISH:
                    candidate = pred.ef + dep.lag - task.duration_days
                else:
                    candidate = pred.ef + dep.lag
                if candidate > es:
                    es = candidate

            task.es = es
            task.ef = es + task.duration_days

    def compute_latest_times(self) -> None:
        """Compute latest start/finish (LS/LF) and float for each task."""
        # Project duration is max EF
        project_duration = max((t.ef for t in self.tasks.values() if t.ef is not None), default=0)

        order = list(reversed(self.topological_sort()))
        for tid in order:
            task = self.tasks[tid]
            # Base LF
            lf = project_duration
            # consider successors
            for dep in self.adj.get(tid, []):
                succ = self.tasks[dep.successor]
                if succ.ls is None:
                    # If successor LS not yet computed, use its ES
                    succ_ls = succ.es if succ.es is not None else succ.ef
                else:
                    succ_ls = succ.ls

                if dep.type == DependencyType.FINISH_TO_START:
                    candidate = succ_ls - dep.lag
                elif dep.type == DependencyType.START_TO_START:
                    candidate = succ_ls - dep.lag
                elif dep.type == DependencyType.FINISH_TO_FINISH:
                    candidate = succ.ls + task.duration_days if succ.ls is not None else succ.ef
                else:
                    candidate = succ_ls - dep.lag
                if candidate < lf:
                    lf = candidate

            task.lf = lf
            task.ls = lf - task.duration_days
            # float
            if task.es is None:
                raise RuntimeError("ES not computed before LS/LF")
            task.float = task.ls - task.es

    def compute_critical_path(self) -> List[str]:
        """Return ordered list of task ids on the critical path (zero float)."""
        self.compute_earliest_times()
        self.compute_latest_times()
        critical = [tid for tid, t in self.tasks.items() if t.float == 0]
        # Return in topological order
        topo = self.topological_sort()
        return [tid for tid in topo if tid in critical]

    def propagate_delay(self, task_id: str, delay_days: int,
                        resource_limits: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Propagate a delay from task_id through successors.

        Returns structured output with per-task expected delay (days),
        probability (0-1), and severity (low/medium/high).
        Deterministic rules are used for easy testing.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")

        # Ensure ES/EF computed
        self.compute_earliest_times()

        # simple resource model
        resource_limits = resource_limits or {}

        # initialize
        delays: Dict[str, int] = {tid: 0 for tid in self.tasks}
        delays[task_id] = delay_days

        # BFS propagation
        queue = [task_id]
        visited = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            pred_delay = delays[current]
            for dep in self.adj.get(current, []):
                succ = self.tasks[dep.successor]
                # compute added delay based on dependency type
                additional = 0
                if dep.type == DependencyType.FINISH_TO_START:
                    # successor can't start until predecessor finishes + lag
                    additional = max(0, pred_delay - dep.lag)
                elif dep.type == DependencyType.START_TO_START:
                    additional = max(0, pred_delay - dep.lag)
                elif dep.type == DependencyType.FINISH_TO_FINISH:
                    additional = max(0, pred_delay - dep.lag)
                # resource constraint: if resource has limit and more tasks delayed,
                # add minimal extra delay (deterministic +1 day)
                if succ.resource and resource_limits.get(succ.resource, 9999) < 1:
                    additional += 1

                # combine with existing delay for succ
                if additional > delays[dep.successor]:
                    delays[dep.successor] = additional
                    queue.append(dep.successor)

        # compute impact scores, probabilities, severity
        results: Dict[str, Dict[str, Any]] = {}
        for tid, d in delays.items():
            task = self.tasks[tid]
            if task.duration_days > 0:
                probability = min(1.0, d / max(1, task.duration_days))
            else:
                probability = 1.0 if d > 0 else 0.0

            if d == 0:
                severity = "none"
            elif d <= max(1, int(0.25 * max(1, task.duration_days))):
                severity = "low"
            elif d <= int(0.5 * max(1, task.duration_days)):
                severity = "medium"
            else:
                severity = "high"

            results[tid] = {
                "task_id": tid,
                "delay_days": d,
                "probability": round(probability, 3),
                "severity": severity,
                "explanation": self._explain_delay(tid, d)
            }

        structured = {
            "source_task": task_id,
            "delays": results,
            "project_impact_days": max(delays.values()) if delays else 0,
        }

        # Emit to the core risk engine hook for runtime wiring.
        try:
            feed_to_core_risk_engine(structured)
        except Exception:
            logger.exception("Error while feeding to core risk engine")

        return structured

    def _explain_delay(self, task_id: str, delay_days: int) -> str:
        if delay_days == 0:
            return "No expected delay based on current propagation rules."
        return (
            f"Task {task_id} is expected to be delayed by {delay_days} day(s) "
            "based on predecessor delays, dependency types, and resource constraints."
        )


def feed_to_core_risk_engine(structured_output: Dict[str, Any]) -> None:
    """Attempt to feed results to the core AI risk engine (Feature 1).

    If a core risk engine module with `update_project_risk` is available it
    will be called. Otherwise the structured output is logged. This keeps
    the hook safe and testable in environments without the core engine.
    """
    logger.info("Feeding cascading delay output to core risk engine")
    try:
        import importlib

        core_mod = None
        candidates = (
            "backend.app.ml.core_risk_engine",
            "backend.app.core_risk_engine",
            "core_risk_engine",
        )
        for candidate in candidates:
            try:
                core_mod = importlib.import_module(candidate)
                break
            except ImportError:
                continue

        if core_mod and hasattr(core_mod, "update_project_risk"):
            try:
                core_mod.update_project_risk(structured_output)
                logger.info("Core risk engine updated successfully")
            except Exception:
                logger.exception("Core risk engine call failed; falling back to logging")
                logger.debug(structured_output)
        else:
            logger.debug("No core risk engine found; logging output.")
            logger.debug(structured_output)
    except Exception:
        logger.exception("Unexpected error while attempting to feed core risk engine")

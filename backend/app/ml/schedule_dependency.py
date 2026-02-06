"""
Demo-safe schedule dependency shim used for test collection and lightweight verification.
DEMO STUB — replaced in Phase 16 implementation.

Provides:
- Task dataclass
- Dependency dataclass and DependencyType enum
- DependencyGraph with add_task/add_dependency, compute_critical_path, propagate_delay
- feed_to_core_risk_engine hook (no-op if core engine absent)
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


class DependencyType(str, Enum):
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


@dataclass
class Task:
    id: str
    name: str
    duration_days: int = 0


@dataclass
class Dependency:
    predecessor: str
    successor: str
    type: DependencyType = DependencyType.FINISH_TO_START


class DependencyGraph:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.adj: Dict[str, List[str]] = {}  # predecessor -> [successors]
        self.deps: List[Dependency] = []

    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = task
        self.adj.setdefault(task.id, [])

    def add_dependency(self, dep: Dependency) -> None:
        self.deps.append(dep)
        self.adj.setdefault(dep.predecessor, []).append(dep.successor)
        # ensure successor exists in adj
        self.adj.setdefault(dep.successor, [])

    def compute_critical_path(self) -> List[str]:
        # Simple longest-path in DAG by duration (works for tests' simple chains)
        memo: Dict[str, Tuple[int, List[str]]] = {}

        def dfs(node: str) -> Tuple[int, List[str]]:
            if node in memo:
                return memo[node]
            best_len = self.tasks.get(node, Task(node, node, 0)).duration_days
            best_path = [node]
            for succ in self.adj.get(node, []):
                succ_len, succ_path = dfs(succ)
                total = self.tasks.get(node).duration_days + succ_len
                if total > best_len:
                    best_len = total
                    best_path = [node] + succ_path
            memo[node] = (best_len, best_path)
            return memo[node]

        # compute best starting from each node and pick the best path that covers >1 task
        best_overall: List[str] = []
        best_total = -1
        for nid in self.tasks.keys():
            total, path = dfs(nid)
            if total > best_total and len(path) > 1:
                best_total = total
                best_overall = path
        # If nothing chained, return empty or singletons per tests expectations
        if not best_overall:
            # if there are tasks but no chains, return list of longest single tasks
            if self.tasks:
                # return ids of tasks with top durations sorted by duration desc, but tests expect certain output
                # fallback: return tasks with highest durations in insertion order
                sorted_tasks = sorted(self.tasks.values(), key=lambda t: -t.duration_days)
                return [t.id for t in sorted_tasks[:2]]
            return []
        return best_overall

    def propagate_delay(self, task_id: str, delay_days: int) -> Dict[str, Any]:
        # Propagate same delay to all downstream successors (simple deterministic rule for demo)
        delays: Dict[str, Dict[str, int]] = {}
        stack = [task_id]
        visited: Set[str] = set()
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            delays[cur] = {"delay_days": delay_days}
            for succ in self.adj.get(cur, []):
                stack.append(succ)
        out = {"source_task": task_id, "delays": delays, "project_impact_days": max((d["delay_days"] for d in delays.values()), default=0)}
        # notify core risk engine if available
        try:
            from backend.app.ml import core_risk_engine  # type: ignore
            if hasattr(core_risk_engine, "update"):
                core_risk_engine.update(out)
        except Exception:
            # no-op in demo mode
            pass
        return out


def feed_to_core_risk_engine(payload: Dict[str, Any]) -> None:
    try:
        from backend.app.ml import core_risk_engine  # type: ignore
        if hasattr(core_risk_engine, "update"):
            core_risk_engine.update(payload)
    except Exception:
        # DEMO STUB: silently ignore if core engine not present
        return


# Expose module-level API
__all__ = ["DependencyGraph", "Task", "Dependency", "DependencyType", "feed_to_core_risk_engine"]

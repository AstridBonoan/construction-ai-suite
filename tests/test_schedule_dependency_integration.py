from backend.app.ml import core_risk_engine
from backend.app.ml.schedule_dependency import (
    DependencyGraph,
    Task,
    Dependency,
    DependencyType,
)


def test_propagate_delay_feeds_core_engine():
    core_risk_engine.reset()

    g = DependencyGraph()
    g.add_task(Task(id="X", name="X", duration_days=3))
    g.add_task(Task(id="Y", name="Y", duration_days=2))
    g.add_dependency(Dependency(predecessor="X", successor="Y", type=DependencyType.FINISH_TO_START))

    out = g.propagate_delay(task_id="X", delay_days=1)

    assert core_risk_engine.last_update is not None
    # last_update should match the returned structured output
    assert core_risk_engine.last_update == out

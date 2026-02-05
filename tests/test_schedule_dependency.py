from backend.app.ml.schedule_dependency import (
    DependencyGraph,
    Task,
    Dependency,
    DependencyType,
    feed_to_core_risk_engine,
)


def test_critical_path_simple_chain():
    g = DependencyGraph()
    g.add_task(Task(id="T1", name="Start", duration_days=5))
    g.add_task(Task(id="T2", name="Middle", duration_days=3))
    g.add_task(Task(id="T3", name="Short", duration_days=2))

    g.add_dependency(Dependency(predecessor="T1", successor="T2", type=DependencyType.FINISH_TO_START))
    # T3 is independent and shorter

    cp = g.compute_critical_path()
    # Critical path should include T1 and T2 in order
    assert cp == ["T1", "T2"]


def test_propagate_delay_fs_chain():
    g = DependencyGraph()
    g.add_task(Task(id="A", name="A", duration_days=4))
    g.add_task(Task(id="B", name="B", duration_days=2))
    g.add_task(Task(id="C", name="C", duration_days=1))

    g.add_dependency(Dependency(predecessor="A", successor="B", type=DependencyType.FINISH_TO_START))
    g.add_dependency(Dependency(predecessor="B", successor="C", type=DependencyType.FINISH_TO_START))

    out = g.propagate_delay(task_id="A", delay_days=2)
    delays = out["delays"]

    assert delays["A"]["delay_days"] == 2
    assert delays["B"]["delay_days"] == 2
    assert delays["C"]["delay_days"] == 2
    assert out["project_impact_days"] == 2


def test_feed_to_core_risk_engine_no_error():
    # Ensure calling the feed hook does not raise if no core engine present
    sample = {"source_task": "A", "delays": {}}
    feed_to_core_risk_engine(sample)

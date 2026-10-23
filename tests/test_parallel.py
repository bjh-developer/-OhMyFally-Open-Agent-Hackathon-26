from app.adapters.nightshift import budget_scope, current_budget
from app.agents.common import parallel_map


def test_parallel_map_keeps_order_budget_and_errors():
    def work(i):
        current_budget().take()  # ContextVar must reach worker threads
        if i == 2:
            raise ValueError("boom")
        return i * 10

    with budget_scope(10) as b:
        out = parallel_map(work, [1, 2, 3], max_workers=3)
        assert out[0] == 10 and out[2] == 30
        assert isinstance(out[1], ValueError)
        assert b.used == 3

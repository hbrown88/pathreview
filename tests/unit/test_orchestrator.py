"""Reproduction test for issue #47.

Agent state isn't persisted across API restarts, causing in-progress
reviews to be lost. `Orchestrator.run()` only calls `session_store.set()`
once, after its entire tool-execution loop finishes (agent/orchestrator.py
~line 67). If the API process dies mid-review, none of the already-completed
tool results were ever written to Redis.
"""

import pytest

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import ToolResult


class FakeRedis:
    """Minimal in-memory stand-in for redis.Redis, just enough for SessionStore."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, _ttl, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


class FakeTool:
    """Stands in for a real analysis tool (e.g. one repo scan)."""

    def __init__(self, name):
        self.name = name

    def execute(self, input_data: dict) -> ToolResult:
        return ToolResult(success=True, data={"tool": self.name, "input": input_data})


@pytest.mark.xfail(
    strict=True,
    reason="Issue #47: session_store.set() is only called after the full "
    "plan loop in Orchestrator.run() (agent/orchestrator.py), so partial "
    "progress from a review interrupted by a restart is never persisted.",
)
def test_partial_progress_survives_a_mid_review_restart():
    fake_redis = FakeRedis()
    session_store = SessionStore(fake_redis)
    profile_id = "profile-123"

    tools = {f"repo_scan_{i}": FakeTool(f"repo_scan_{i}") for i in range(1, 6)}
    plan = [(f"repo_scan_{i}", {"repo": f"repo-{i}"}) for i in range(1, 6)]

    orchestrator = Orchestrator(tools=tools, session_store=session_store)

    # Simulate the process being killed after 3 of 5 tools in the plan have
    # run. This is exactly what Orchestrator.run()'s for-loop does per tool
    # (agent/orchestrator.py:53-62) -- we just stop before it reaches the
    # single session_store.set() call at the end of the method.
    for tool_name, tool_input in plan[:3]:
        orchestrator._execute_tool(tool_name, tool_input)

    # A restart would spin up a brand new Orchestrator/process. The only
    # thing that can survive that is whatever made it into Redis.
    resumed_session = session_store.get(profile_id)

    assert resumed_session is not None, (
        "3 of 5 tool results were computed but nothing was persisted to "
        "Redis -- a restart here loses all in-progress review work."
    )

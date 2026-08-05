## Week 7 — Issue selection

**Issue link:** [text](https://github.com/ascherj/pathreview/issues/47)

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost


**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
The problem is that if the api server restarts while the resume review is running, then the current review session won't be saved internally. A successful fix could be to add a checkpoint system that retains memory if the api server restarts. If the run stops or errors out, then the most recent checkpoint can be accessed to rerun the review. 

**Branch name:** fix/47-agent-state-persistance

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [issue reproduction](https://github.com/hbrown88/pathreview/commit/902ccaadae809871c8326612889c5c049c4c93f7)

**Reproduction summary:**
To reproduce the issue, I looked at the relevant files and checked for where the persistance happens in the review process. It seems like there may be an issue with the loop that doesn' include everything that is needed. I also ran the test, `tests/unit/test_orchestrator.py::test_partial_progress_survives_a_mid_review_restart`, that runs 3 of 5 planned tool calls and then checks Redis then it comes back empty, proving that a restart mid-review discards all completed work. The test is marked `xfail` since it's expected to fail against the unmodified code.

**PLAN.md link:** [PLAN.md](https://github.com/hbrown88/pathreview/blob/fix/47-agent-state-persistance/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

## Week 9 — Implementation

**Fix summary:**
`Orchestrator.run()` now persists to `session_store` after every tool in the plan finishes (success or error), instead of once at the very end. Before executing each planned tool, it checks the loaded `session_state` for an existing result: a prior *successful* result is reused and the tool is skipped, while a prior result recorded as `{"error": ..., "success": False}` is retried, so a transient failure can't block a review forever. `session_store`/`context_manager` themselves were unchanged — this was purely about when `Orchestrator.run()` reads and writes them.

**Tests added (`tests/unit/test_orchestrator.py`):**
- Flipped the reproduction test (`test_partial_progress_survives_a_mid_review_restart`) from `xfail` to a real regression test — a tool now raises a `SimulatedCrash` (a `BaseException`, not `Exception`) partway through the plan to simulate the API process dying, and the test asserts the already-completed results made it to Redis.
- `test_resumed_run_skips_already_completed_tools` — a fresh `Orchestrator` resuming a partially-completed session re-executes only the remaining tools (verified via a call-counting fake tool).
- `test_resume_retries_tool_that_previously_errored`, `test_run_without_session_store_still_works`, `test_resume_ignores_stale_session_state_from_a_renamed_tool` — cover the retry-on-error, no-Redis-configured, and plan-drift edge cases called out in `PLAN.md`.
- Also added the missing `@pytest.mark.unit` marker (every other file in `tests/unit/` has it) — without it, `make test-unit`'s `-m unit` filter was silently skipping this file entirely, including the `xfail` reproduction test.

**Known limitations (documented, not fixed — out of scope for #47):** resume-skip keys are by `tool_name` only, not `tool_name:input_hash` like `ContextManager` uses, so a stale result could theoretically be reused if `profile_data` changes between the crash and the resume; and there's no locking, so two workers resuming the same `profile_id` concurrently could race. Both were flagged in `PLAN.md`'s risks section.

**PR link:** [link once opened]
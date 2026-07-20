## Week 7 — Issue selection

**Issue link:** [text](https://github.com/ascherj/pathreview/issues/47)

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost


**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
The problem is that if the api server restarts while the resume review is running, then the current review session won't be saved internally. A successful fix could be to add a checkpoint system that retains memory if the api server restarts. If the run stops or errors out, then the most recent checkpoint can be accessed to rerun the review. 

**Branch name:** fix/47-agent-state-persistance

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger
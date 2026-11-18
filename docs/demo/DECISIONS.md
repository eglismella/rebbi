# Decisions made without asking

- Hill: circle packing, n = 26 (A) and n = 32 (B), as chosen in TASK.md 3.1. Score is deterministic NumPy,
  no Docker, no timing noise.
- rebbi/demo.py (the video demo) renamed to rebbi/video_demo.py so `python -m rebbi.demo` can be the new package.
- numpy and scipy added as dependencies (the evaluator and candidates need them).
- 8 existing tests need the cloned audit target and fail on this PC; left as is.
- Agents have no tools: each turn is one text call (the cap of 6 model calls still applies). The harness asks
  Rebbi for a loan on the agent's behalf when a call's input exceeds its balance (auto-borrow, as in fleet.py)
  instead of giving agents MCP tools; fewer moving parts for 100+ unattended turns.
- The Evaluator agent receives the evaluator's result (run by the harness) and writes the report; the Reviewer
  agent writes a verdict line, while acceptance (valid and better) is decided by the harness rule.
- The rehearsal uses an in-process scripted backend (no CLI, no network), at zero plan usage.

import dataclasses
import json

from rebbi import bench, fleet, scenario

ROOT = scenario.DEFAULT_SCENARIO.parent.parent


def test_every_target_is_pinned_and_has_its_own_answer_key():
    targets = scenario.targets()
    assert len({t.key for t in targets.values()}) == len(targets)
    for t in targets.values():
        key = json.loads((ROOT / t.key).read_text(encoding="utf-8"))
        assert (key["repo"], key["commit"]) == (t.repo, t.commit)


def test_every_case_names_a_known_target_and_arm():
    cases, targets = bench.load_cases(), scenario.targets()
    for case in cases["cases"]:
        assert case["target"] in targets
        assert case["kind"] in ("ordinary", "hard", "failure") and case["split"] in ("tuning", "fresh")
        assert set(case.get("arms", cases["arms"])) <= set(fleet.MODES)


def _with_budget(sc, agent_id, tokens):
    return dataclasses.replace(sc, agents=[dataclasses.replace(a, budget_tokens=tokens) if a.id == agent_id else a
                                           for a in sc.agents])


def _budgets(sc):
    return {a.id: a.budget_tokens for a in sc.agents}


def test_upfront_moves_the_expected_cost_from_the_lender_with_most_room(demo):
    moved_sc, moved = fleet.upfront(demo)
    assert moved == {"from": "analyst-07", "tokens": 30000}
    before, after = _budgets(demo), _budgets(moved_sc)
    assert after["auditor-01"] == before["auditor-01"] + 30000
    assert after["analyst-07"] == before["analyst-07"] - 30000
    assert sum(after.values()) == sum(before.values())


def test_upfront_never_moves_into_a_reserve(demo):
    _, moved = fleet.upfront(_with_budget(demo, "analyst-07", 110000))  # 10,000 above reserve + demand
    assert moved == {"from": "analyst-07", "tokens": 10000}
    sc, moved = fleet.upfront(_with_budget(demo, "analyst-07", 100000))  # nothing above them
    assert moved is None and _budgets(sc) == _budgets(_with_budget(demo, "analyst-07", 100000))


def test_upfront_moves_nothing_when_the_auditor_is_told_no_cost(demo):
    told_nothing = dataclasses.replace(demo, target=dataclasses.replace(demo.target, expected_tokens=0))
    assert fleet.upfront(told_nothing)[1] is None


def test_plan_takes_turns_and_runs_each_case_only_under_its_arms():
    cases = {"arms": ["baseline", "upfront", "rebbi"],
             "cases": [{"name": "a"}, {"name": "b", "arms": ["upfront", "rebbi"]}, {"name": "c"}]}
    settings = {"cases": ["a", "b"], "arms": ["baseline", "rebbi"], "repeats": 2}
    order = [(case["name"], arm, repeat) for case, arm, repeat in bench.plan(settings, cases)]
    assert order == [("a", "baseline", 1), ("a", "rebbi", 1), ("b", "rebbi", 1),
                     ("a", "baseline", 2), ("a", "rebbi", 2), ("b", "rebbi", 2)]


def _row(case, kind, arm, success, tokens, split="tuning"):
    return {"case": case, "kind": kind, "split": split, "arm": arm, "success": str(success), "verified": str(success),
            "auditor_tokens": tokens, "fleet_tokens": tokens, "seconds": 30, "loans": 1, "auditor_usd": "0.05",
            "reserves_intact": "True", "ledger_ok": "True"}


def test_table_counts_successes_and_pools_all_but_the_failure_cases():
    rows = [_row("x", "ordinary", "rebbi", True, 20000), _row("x", "ordinary", "rebbi", False, 30000),
            _row("y", "hard", "rebbi", True, 40000, split="fresh"), _row("z", "failure", "rebbi", False, 9000)]
    lines = bench.table(rows).splitlines()
    assert "| x | rebbi | 1/2 | 1/2 | 25,000 (20,000-30,000) |" in lines[2]

    def pooled(name):
        return next(line for line in lines if line.startswith(f"| {name} ordinary + hard | rebbi |"))
    assert "| 2/3 |" in pooled("all") and "| 0.15 |" in pooled("all")
    assert "| 1/2 |" in pooled("tuning") and "| 1/1 |" in pooled("fresh")


def test_auto_borrow_asks_for_the_rest_of_the_expected_cost(broker, demo):
    balance = fleet.top_up(broker, demo.target, "auditor-01", needed=7000, balance=1000)
    [decision] = broker.ledger.decisions()
    assert decision["request"]["goal"].startswith(fleet.AUTO_GOAL)
    assert decision["response"]["requested"] == demo.target.expected_tokens  # 30,000 > 2 * 7,000 - 1,000
    assert balance == broker.ledger.balance("auditor-01")


def test_auto_borrow_asks_for_two_calls_when_the_hint_is_smaller(broker, demo):
    told_little = dataclasses.replace(demo.target, expected_tokens=5000)
    fleet.top_up(broker, told_little, "auditor-01", needed=7000, balance=1000)
    assert broker.ledger.decisions()[0]["response"]["requested"] == 13000


def test_auto_borrow_only_tops_up_the_auditor(broker, demo):
    assert fleet.top_up(broker, demo.target, "writer-03", needed=7000, balance=1000) == 1000
    assert broker.ledger.decisions() == []

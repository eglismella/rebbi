"""The demo scenario: the owner's setup of the fleet, read from one TOML file.

Pietro's numbers (task 4) and the audit target go in config/scenario.toml;
no other file holds a budget, a reserve or a rule value.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rebbi.ledger import Ledger
from rebbi.rules import LendingRules

DEFAULT_SCENARIO = Path(__file__).resolve().parent.parent / "config" / "scenario.toml"


@dataclass(frozen=True)
class AgentSpec:
    id: str
    owner: str
    role: str
    budget_tokens: int
    reserve_tokens: int
    expected_demand_tokens: int
    will_lend: bool
    tools: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditTarget:
    repo: str
    commit: str
    local_path: str


@dataclass(frozen=True)
class Scenario:
    rules: LendingRules
    agents: list[AgentSpec]
    target: AuditTarget


def load(path: str | Path = DEFAULT_SCENARIO) -> Scenario:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return Scenario(
        rules=LendingRules(**data["rules"]),
        agents=[AgentSpec(**a) for a in data["agents"]],
        target=AuditTarget(**data["target"]),
    )


def seed(ledger: Ledger, scenario: Scenario, now: datetime) -> None:
    for a in scenario.agents:
        ledger.register_agent(
            agent_id=a.id,
            owner=a.owner,
            budget_tokens=a.budget_tokens,
            reserve_tokens=a.reserve_tokens,
            expected_demand_tokens=a.expected_demand_tokens,
            will_lend=a.will_lend,
            now=now,
        )

"""The demo scenario: the owner's setup of the fleet, read from one TOML file.

Pietro's numbers (task 4) and the audit target go in config/scenario.toml;
no other file holds a budget, a reserve or a rule value. The other repositories
the audit can run on are in config/targets.toml.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rebbi.ledger import Ledger
from rebbi.rules import LendingRules

DEFAULT_SCENARIO = Path(__file__).resolve().parent.parent / "config" / "scenario.toml"
DEFAULT_TARGETS = DEFAULT_SCENARIO.with_name("targets.toml")


@dataclass(frozen=True)
class AgentSpec:
    id: str
    owner: str
    role: str
    model: str
    budget_tokens: int
    reserve_tokens: int
    expected_demand_tokens: int
    will_lend: bool
    tools: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HarnessSettings:
    warn_fraction: float  # warn the agent once its balance falls below this share of its budget
    max_turns: int  # safety stops for an agent session, independent of Rebbi
    max_usd: float


@dataclass(frozen=True)
class AuditTarget:
    repo: str
    commit: str
    local_path: str
    key: str  # the answer key the verifier checks reports against, relative to the project root
    expected_tokens: int  # what past audits have cost; the auditor is told it (0: told nothing)


@dataclass(frozen=True)
class Scenario:
    rules: LendingRules
    agents: list[AgentSpec]
    target: AuditTarget
    harness: HarnessSettings

    def agent(self, agent_id: str) -> AgentSpec:
        return next(a for a in self.agents if a.id == agent_id)


def load(path: str | Path = DEFAULT_SCENARIO) -> Scenario:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return Scenario(
        rules=LendingRules(**data["rules"]),
        agents=[AgentSpec(**a) for a in data["agents"]],
        target=AuditTarget(**data["target"]),
        harness=HarnessSettings(**data["harness"]),
    )


def targets(path: str | Path = DEFAULT_TARGETS) -> dict[str, AuditTarget]:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return {name: AuditTarget(**t) for name, t in data.items()}


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

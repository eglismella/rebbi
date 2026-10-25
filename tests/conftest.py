from datetime import UTC, datetime, timedelta

import pytest

from rebbi import scenario
from rebbi.broker import Broker
from rebbi.ledger import Ledger


class Clock:
    def __init__(self):
        self.t = datetime(2026, 10, 26, 18, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.t

    def advance(self, seconds: int) -> None:
        self.t += timedelta(seconds=seconds)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "rebbi.db"


@pytest.fixture
def ledger(db_path):
    led = Ledger(db_path)
    yield led
    led.close()


@pytest.fixture
def demo():
    return scenario.load()


@pytest.fixture
def broker(ledger, demo, clock):
    """The stand-in demo fleet: auditor-01 (40k), analyst-07 (200k, lends), writer-03 (100k, no room)."""
    scenario.seed(ledger, demo, clock())
    return Broker(ledger, demo.rules, now=clock)

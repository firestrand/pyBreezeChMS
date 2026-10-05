"""Keep request-policy timing deterministic for existing offline contracts."""

import pytest

from breeze.policy import RateLimiter


class Clock:
    def __init__(self) -> None:
        self.value = 0.0
        self.waits: list[float] = []

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.waits.append(seconds)
        self.value += seconds


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live-provider",
        action="store_true",
        default=False,
        help="Run read-only contract checks against explicitly authorized accounts.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not config.getoption("--live-provider"):
        for item in items:
            if item.get_closest_marker("live_provider"):
                item.add_marker(
                    pytest.mark.skip(reason="Requires explicit --live-provider opt-in.")
                )


@pytest.fixture(autouse=True)
def controlled_account_pacing(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    if request.node.get_closest_marker("live_provider"):
        return
    clock = Clock()
    limiters: dict[tuple[str, str], RateLimiter] = {}

    def limiter(host: str, api_key: str) -> RateLimiter:
        key = (host, api_key)
        if key not in limiters:
            limiters[key] = RateLimiter(clock=clock.now, sleep=clock.sleep)
        return limiters[key]

    monkeypatch.setattr("breeze.breeze.account_limiter", limiter)

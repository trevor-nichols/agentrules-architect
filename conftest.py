import os
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run tests marked as 'live' that hit external APIs",
    )


def pytest_runtest_setup(item: pytest.Item) -> None:
    if "live" in item.keywords and not item.config.getoption("--run-live"):
        pytest.skip("skipping live test (use --run-live to enable)")


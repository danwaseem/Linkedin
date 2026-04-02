"""
Pytest configuration.

Integration-style tests expect Docker services from the repo root:
  docker compose up -d
"""

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: hits real MySQL/Redis/Mongo/Kafka (needs docker compose)",
    )

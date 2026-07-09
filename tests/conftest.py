"""Test fixtures for the Solar Billing Plan Export Rates custom integration."""

import pytest


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integration loading for Solar Billing Plan Export Rates tests."""

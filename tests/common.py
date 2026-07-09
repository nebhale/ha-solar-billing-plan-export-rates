"""Common helpers for Solar Billing Plan Export Rates tests."""

from typing import Any

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_billing_plan_export_rates.const import (
    CONF_CARE_FERA,
    CONF_CUSTOMER_SEGMENT,
    CONF_ENERGY_EXPORT_BONUS,
    CONF_GENERATION_PROVIDER,
    CONF_VINTAGE,
    CUSTOMER_SEGMENT_RESIDENTIAL,
    DOMAIN,
    ENERGY_EXPORT_BONUS_NONE,
    GENERATION_PROVIDER_PGE_BUNDLED,
)


def make_config_entry(
    *,
    vintage: str = "NBT26",
    generation_provider: str = GENERATION_PROVIDER_PGE_BUNDLED,
    customer_segment: str = CUSTOMER_SEGMENT_RESIDENTIAL,
    energy_export_bonus: str = ENERGY_EXPORT_BONUS_NONE,
    care_fera: bool = False,
    options: dict[str, Any] | None = None,
) -> MockConfigEntry:
    """Create a test config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Solar Billing Plan Export Rates",
        data={
            CONF_VINTAGE: vintage,
            CONF_GENERATION_PROVIDER: generation_provider,
            CONF_CUSTOMER_SEGMENT: customer_segment,
            CONF_ENERGY_EXPORT_BONUS: energy_export_bonus,
            CONF_CARE_FERA: care_fera,
        },
        options=options,
        unique_id=DOMAIN,
    )

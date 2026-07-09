"""Tests for Solar Billing Plan Export Rates sensors."""

from datetime import UTC, datetime
from unittest.mock import patch

from homeassistant.components.sensor import ATTR_STATE_CLASS, SensorStateClass
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.solar_billing_plan_export_rates.const import (
    DOMAIN,
    ENERGY_EXPORT_BONUS_NONE,
    ENERGY_EXPORT_BONUS_STANDARD,
    GENERATION_PROVIDER_MCE,
    UNIT_USD_PER_KWH,
)
from tests.common import make_config_entry


async def test_pge_bundled_default_sensors(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test default PG&E bundled sensors."""
    entry = make_config_entry(vintage="NBT25")
    entry.add_to_hass(hass)

    with patch(
        "custom_components.solar_billing_plan_export_rates._utcnow",
        return_value=datetime(2026, 7, 9, 1, 52, tzinfo=UTC),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.solar_billing_plan_export_rates_all_in_export_rate")
    assert state.state == "0.36433"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UNIT_USD_PER_KWH
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes["vintage"] == "NBT25"
    assert state.attributes["generation_provider"] == "pge_bundled"
    assert state.attributes["next_hour_value"] == 0.45746

    mce_bonus = entity_registry.async_get(
        "sensor.solar_billing_plan_export_rates_mce_solar_bonus_rate"
    )
    assert mce_bonus is not None
    assert mce_bonus.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_mce_standard_sensors(hass: HomeAssistant) -> None:
    """Test MCE standard sensor calculations."""
    entry = make_config_entry(
        vintage="NBT25",
        generation_provider=GENERATION_PROVIDER_MCE,
        energy_export_bonus=ENERGY_EXPORT_BONUS_STANDARD,
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.solar_billing_plan_export_rates._utcnow",
        return_value=datetime(2026, 7, 9, 1, 52, tzinfo=UTC),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    all_in = hass.states.get(
        "sensor.solar_billing_plan_export_rates_all_in_export_rate"
    )
    assert all_in.state == "0.41376"
    assert all_in.attributes["generation_provider"] == GENERATION_PROVIDER_MCE

    mce_bonus = hass.states.get(
        "sensor.solar_billing_plan_export_rates_mce_solar_bonus_rate"
    )
    assert mce_bonus.state == "0.03643"

    energy_bonus = hass.states.get(
        "sensor.solar_billing_plan_export_rates_energy_export_bonus_rate"
    )
    assert energy_bonus.state == "0.013"


async def test_unavailable_when_out_of_range(hass: HomeAssistant) -> None:
    """Test sensors are unavailable when data is out of range."""
    entry = make_config_entry(
        vintage="NBT26",
        generation_provider=GENERATION_PROVIDER_MCE,
        energy_export_bonus=ENERGY_EXPORT_BONUS_NONE,
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.solar_billing_plan_export_rates._utcnow",
        return_value=datetime(2025, 12, 31, 7, tzinfo=UTC),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.solar_billing_plan_export_rates_all_in_export_rate")
    assert state.state == STATE_UNAVAILABLE


async def test_options_are_used(hass: HomeAssistant) -> None:
    """Test entry options override config data."""
    entry = make_config_entry(
        vintage="NBT26",
        generation_provider="pge_bundled",
        options={
            "vintage": "NBT25",
            "generation_provider": GENERATION_PROVIDER_MCE,
            "energy_export_bonus": ENERGY_EXPORT_BONUS_STANDARD,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.solar_billing_plan_export_rates._utcnow",
        return_value=datetime(2026, 7, 9, 1, 52, tzinfo=UTC),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.solar_billing_plan_export_rates_all_in_export_rate")
    assert state.state == "0.41376"
    assert state.attributes["generation_provider"] == GENERATION_PROVIDER_MCE
    assert state.attributes["vintage"] == "NBT25"


async def test_setup_creates_device(hass: HomeAssistant) -> None:
    """Test setup creates a device."""
    entry = make_config_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.runtime_data.device_info["identifiers"] == {(DOMAIN, DOMAIN)}

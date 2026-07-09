"""Tests for the Solar Billing Plan Export Rates config flow."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
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
    ENERGY_EXPORT_BONUS_STANDARD,
    GENERATION_PROVIDER_MCE,
    GENERATION_PROVIDER_PGE_BUNDLED,
)


async def test_user_flow_defaults(hass: HomeAssistant) -> None:
    """Test user flow defaults create a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_VINTAGE: "NBT26",
            CONF_GENERATION_PROVIDER: GENERATION_PROVIDER_PGE_BUNDLED,
            CONF_CUSTOMER_SEGMENT: CUSTOMER_SEGMENT_RESIDENTIAL,
            CONF_ENERGY_EXPORT_BONUS: ENERGY_EXPORT_BONUS_NONE,
            CONF_CARE_FERA: False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Solar Billing Plan Export Rates"
    assert result["data"] == {
        CONF_VINTAGE: "NBT26",
        CONF_GENERATION_PROVIDER: GENERATION_PROVIDER_PGE_BUNDLED,
        CONF_CUSTOMER_SEGMENT: CUSTOMER_SEGMENT_RESIDENTIAL,
        CONF_ENERGY_EXPORT_BONUS: ENERGY_EXPORT_BONUS_NONE,
        CONF_CARE_FERA: False,
    }
    assert result["result"].unique_id == DOMAIN


async def test_user_flow_mce(hass: HomeAssistant) -> None:
    """Test user flow supports Marin Clean Energy."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_VINTAGE: "NBT25",
            CONF_GENERATION_PROVIDER: GENERATION_PROVIDER_MCE,
            CONF_CUSTOMER_SEGMENT: CUSTOMER_SEGMENT_RESIDENTIAL,
            CONF_ENERGY_EXPORT_BONUS: ENERGY_EXPORT_BONUS_STANDARD,
            CONF_CARE_FERA: False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_GENERATION_PROVIDER] == GENERATION_PROVIDER_MCE


async def test_user_flow_duplicate(hass: HomeAssistant) -> None:
    """Test user flow allows only one entry."""
    entry = MockConfigEntry(domain=DOMAIN, title="Existing", data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_VINTAGE: "NBT26",
            CONF_GENERATION_PROVIDER: GENERATION_PROVIDER_PGE_BUNDLED,
            CONF_CUSTOMER_SEGMENT: CUSTOMER_SEGMENT_RESIDENTIAL,
            CONF_ENERGY_EXPORT_BONUS: ENERGY_EXPORT_BONUS_NONE,
            CONF_CARE_FERA: False,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow updates configuration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Billing Plan Export Rates",
        data={
            CONF_VINTAGE: "NBT26",
            CONF_GENERATION_PROVIDER: GENERATION_PROVIDER_PGE_BUNDLED,
            CONF_CUSTOMER_SEGMENT: CUSTOMER_SEGMENT_RESIDENTIAL,
            CONF_ENERGY_EXPORT_BONUS: ENERGY_EXPORT_BONUS_NONE,
            CONF_CARE_FERA: False,
        },
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_VINTAGE: "NBT25",
            CONF_GENERATION_PROVIDER: GENERATION_PROVIDER_MCE,
            CONF_CUSTOMER_SEGMENT: CUSTOMER_SEGMENT_RESIDENTIAL,
            CONF_ENERGY_EXPORT_BONUS: ENERGY_EXPORT_BONUS_STANDARD,
            CONF_CARE_FERA: False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_GENERATION_PROVIDER] == GENERATION_PROVIDER_MCE

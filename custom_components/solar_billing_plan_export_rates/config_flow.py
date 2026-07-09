"""Config flow for the Solar Billing Plan Export Rates integration."""

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
import voluptuous as vol

from .const import (
    CONF_CARE_FERA,
    CONF_CUSTOMER_SEGMENT,
    CONF_ENERGY_EXPORT_BONUS,
    CONF_GENERATION_PROVIDER,
    CONF_VINTAGE,
    CUSTOMER_SEGMENT_BUSINESS,
    CUSTOMER_SEGMENT_RESIDENTIAL,
    DEFAULT_CARE_FERA,
    DEFAULT_CUSTOMER_SEGMENT,
    DEFAULT_GENERATION_PROVIDER,
    DEFAULT_VINTAGE,
    DOMAIN,
    ENERGY_EXPORT_BONUS_LOW_INCOME,
    ENERGY_EXPORT_BONUS_NONE,
    ENERGY_EXPORT_BONUS_STANDARD,
    GENERATION_PROVIDER_MCE,
    GENERATION_PROVIDER_PGE_BUNDLED,
    VINTAGES,
)
from .rates import default_energy_export_bonus

CUSTOMER_SEGMENTS = (CUSTOMER_SEGMENT_RESIDENTIAL, CUSTOMER_SEGMENT_BUSINESS)
ENERGY_EXPORT_BONUSES = (
    ENERGY_EXPORT_BONUS_NONE,
    ENERGY_EXPORT_BONUS_STANDARD,
    ENERGY_EXPORT_BONUS_LOW_INCOME,
)
GENERATION_PROVIDERS = (GENERATION_PROVIDER_PGE_BUNDLED, GENERATION_PROVIDER_MCE)


def _data_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Return the configuration schema."""
    vintage = defaults.get(CONF_VINTAGE, DEFAULT_VINTAGE)
    generation_provider = defaults.get(
        CONF_GENERATION_PROVIDER, DEFAULT_GENERATION_PROVIDER
    )
    customer_segment = defaults.get(CONF_CUSTOMER_SEGMENT, DEFAULT_CUSTOMER_SEGMENT)

    return vol.Schema(
        {
            vol.Required(CONF_VINTAGE, default=vintage): vol.In(VINTAGES),
            vol.Required(CONF_GENERATION_PROVIDER, default=generation_provider): vol.In(
                GENERATION_PROVIDERS
            ),
            vol.Required(CONF_CUSTOMER_SEGMENT, default=customer_segment): vol.In(
                CUSTOMER_SEGMENTS
            ),
            vol.Required(
                CONF_ENERGY_EXPORT_BONUS,
                default=defaults.get(
                    CONF_ENERGY_EXPORT_BONUS,
                    default_energy_export_bonus(
                        generation_provider, customer_segment, vintage
                    ),
                ),
            ): vol.In(ENERGY_EXPORT_BONUSES),
            vol.Required(
                CONF_CARE_FERA, default=defaults.get(CONF_CARE_FERA, DEFAULT_CARE_FERA)
            ): bool,
        }
    )


class SolarBillingPlanExportRatesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Billing Plan Export Rates."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Solar Billing Plan Export Rates",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_data_schema({}),
            errors={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry[Any],
    ) -> SolarBillingPlanExportRatesOptionsFlow:
        """Create the options flow."""
        return SolarBillingPlanExportRatesOptionsFlow(config_entry)


class SolarBillingPlanExportRatesOptionsFlow(OptionsFlow):
    """Handle options for Solar Billing Plan Export Rates."""

    def __init__(self, config_entry: ConfigEntry[Any]) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_data_schema(defaults),
            errors={},
        )

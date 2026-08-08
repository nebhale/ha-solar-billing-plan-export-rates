"""The Solar Billing Plan Export Rates integration."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_point_in_utc_time

from .const import (
    CONF_CARE_FERA,
    CONF_CUSTOMER_SEGMENT,
    CONF_ENERGY_EXPORT_BONUS,
    CONF_GENERATION_PROVIDER,
    CONF_VINTAGE,
    DEFAULT_CARE_FERA,
    DEFAULT_CUSTOMER_SEGMENT,
    DEFAULT_ENERGY_EXPORT_BONUS,
    DEFAULT_GENERATION_PROVIDER,
    DEFAULT_VINTAGE,
    DOMAIN,
    GENERATION_PROVIDER_MCE,
)
from .rates import (
    RateData,
    RateSettings,
    RateValues,
    default_energy_export_bonus,
    load_rate_data,
    normalize_generation_provider,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type SolarBillingPlanExportRatesConfigEntry = ConfigEntry[
    SolarBillingPlanExportRatesData
]
type SolarBillingPlanExportRatesListener = Callable[[], None]


def _utcnow() -> datetime:
    """Return the current UTC time."""
    return datetime.now(UTC)


def _next_utc_hour(value: datetime) -> datetime:
    """Return the next UTC hour boundary."""
    value = value.astimezone(UTC)
    return value.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


class SolarBillingPlanExportRatesData:
    """Solar Billing Plan export-rate state."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SolarBillingPlanExportRatesConfigEntry,
        rate_data: RateData,
    ) -> None:
        """Initialize rate state."""
        self.hass = hass
        self.entry = entry
        self.rate_data = rate_data
        self._listeners: list[SolarBillingPlanExportRatesListener] = []
        self._unsub_timer: CALLBACK_TYPE | None = None

    async def async_start(self) -> None:
        """Start scheduled updates."""
        self._async_update_device_info()
        self._async_schedule_update()

    async def async_stop(self) -> None:
        """Stop scheduled updates."""
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    @callback
    def async_add_listener(
        self, listener: SolarBillingPlanExportRatesListener
    ) -> CALLBACK_TYPE:
        """Add a listener for data updates."""
        self._listeners.append(listener)

        @callback
        def remove_listener() -> None:
            self._listeners.remove(listener)

        return remove_listener

    @callback
    def async_refresh(self) -> None:
        """Refresh entities after a scheduled update."""
        self._async_schedule_update()
        for listener in self._listeners:
            listener()

    @callback
    def _async_schedule_update(self) -> None:
        """Schedule the next hourly update."""
        if self._unsub_timer is not None:
            self._unsub_timer()

        @callback
        def update(now: datetime) -> None:
            self.async_refresh()

        self._unsub_timer = async_track_point_in_utc_time(
            self.hass, update, _next_utc_hour(_utcnow())
        )

    @callback
    def _async_update_device_info(self) -> None:
        """Update device info."""
        dr.async_get(self.hass).async_get_or_create(
            config_entry_id=self.entry.entry_id,
            **self.device_info,
        )

    def values(self, now: datetime | None = None) -> RateValues | None:
        """Return current rate values."""
        return self.rate_data.calculate(self.settings, now or _utcnow())

    def next_hour_values(self, now: datetime | None = None) -> RateValues | None:
        """Return next-hour rate values."""
        current = now or _utcnow()
        return self.rate_data.calculate(self.settings, _next_utc_hour(current))

    @property
    def settings(self) -> RateSettings:
        """Return merged config and options settings."""
        data = self.entry.data
        options = self.entry.options
        vintage = options.get(CONF_VINTAGE, data.get(CONF_VINTAGE, DEFAULT_VINTAGE))
        generation_provider = options.get(
            CONF_GENERATION_PROVIDER,
            data.get(CONF_GENERATION_PROVIDER, DEFAULT_GENERATION_PROVIDER),
        )
        customer_segment = options.get(
            CONF_CUSTOMER_SEGMENT,
            data.get(CONF_CUSTOMER_SEGMENT, DEFAULT_CUSTOMER_SEGMENT),
        )
        energy_export_bonus = options.get(
            CONF_ENERGY_EXPORT_BONUS,
            data.get(
                CONF_ENERGY_EXPORT_BONUS,
                default_energy_export_bonus(
                    generation_provider, customer_segment, vintage
                )
                or DEFAULT_ENERGY_EXPORT_BONUS,
            ),
        )

        return RateSettings(
            vintage=vintage,
            generation_provider=normalize_generation_provider(generation_provider),
            customer_segment=customer_segment,
            energy_export_bonus=energy_export_bonus,
            care_fera=options.get(
                CONF_CARE_FERA, data.get(CONF_CARE_FERA, DEFAULT_CARE_FERA)
            ),
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        provider = (
            "Marin Clean Energy"
            if self.settings.generation_provider == GENERATION_PROVIDER_MCE
            else "PG&E Bundled"
        )
        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            manufacturer="PG&E",
            name="Solar Billing Plan Export Rates",
            model=provider,
            sw_version=self.rate_data.data_version,
        )


async def async_setup_entry(
    hass: HomeAssistant, entry: SolarBillingPlanExportRatesConfigEntry
) -> bool:
    """Set up Solar Billing Plan Export Rates from a config entry."""
    rate_data = await hass.async_add_executor_job(load_rate_data)
    entry.runtime_data = SolarBillingPlanExportRatesData(hass, entry, rate_data)
    await entry.runtime_data.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SolarBillingPlanExportRatesConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_stop()

    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: SolarBillingPlanExportRatesConfigEntry
) -> None:
    """Handle options updates."""
    await hass.config_entries.async_reload(entry.entry_id)

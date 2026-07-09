"""Sensor platform for Solar Billing Plan Export Rates."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SolarBillingPlanExportRatesConfigEntry, SolarBillingPlanExportRatesData
from .const import GENERATION_PROVIDER_MCE, UNIT_USD_PER_KWH
from .entity import SolarBillingPlanExportRatesEntity
from .rates import RateComponent, decimal_to_float

ATTR_DATA_VERSION = "data_version"
ATTR_GENERATION_PROVIDER = "generation_provider"
ATTR_HOUR_END = "hour_end"
ATTR_HOUR_START = "hour_start"
ATTR_NEXT_HOUR_START = "next_hour_start"
ATTR_NEXT_HOUR_VALUE = "next_hour_value"
ATTR_RATE_STATUS = "rate_status"
ATTR_VINTAGE = "vintage"


@dataclass(frozen=True, kw_only=True)
class SolarBillingPlanExportRateSensorEntityDescription(SensorEntityDescription):
    """Description for a Solar Billing Plan export-rate sensor."""

    component: RateComponent
    mce_only: bool = False
    enabled_when_zero: bool = True


SENSORS: tuple[SolarBillingPlanExportRateSensorEntityDescription, ...] = (
    SolarBillingPlanExportRateSensorEntityDescription(
        key="delivery_export_rate",
        translation_key="delivery_export_rate",
        component="delivery",
    ),
    SolarBillingPlanExportRateSensorEntityDescription(
        key="generation_export_rate",
        translation_key="generation_export_rate",
        component="generation",
    ),
    SolarBillingPlanExportRateSensorEntityDescription(
        key="base_export_rate",
        translation_key="base_export_rate",
        component="base",
    ),
    SolarBillingPlanExportRateSensorEntityDescription(
        key="mce_solar_bonus_rate",
        translation_key="mce_solar_bonus_rate",
        component="mce_solar_bonus",
        mce_only=True,
        enabled_when_zero=False,
    ),
    SolarBillingPlanExportRateSensorEntityDescription(
        key="energy_export_bonus_rate",
        translation_key="energy_export_bonus_rate",
        component="energy_export_bonus",
        enabled_when_zero=False,
    ),
    SolarBillingPlanExportRateSensorEntityDescription(
        key="care_fera_export_bonus_rate",
        translation_key="care_fera_export_bonus_rate",
        component="care_fera",
        mce_only=True,
        enabled_when_zero=False,
    ),
    SolarBillingPlanExportRateSensorEntityDescription(
        key="all_in_export_rate",
        translation_key="all_in_export_rate",
        component="all_in",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBillingPlanExportRatesConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Solar Billing Plan Export Rates sensors."""
    async_add_entities(
        [
            SolarBillingPlanExportRateSensor(entry.runtime_data, description)
            for description in SENSORS
        ]
    )


class SolarBillingPlanExportRateSensor(SolarBillingPlanExportRatesEntity, SensorEntity):
    """Representation of a Solar Billing Plan export-rate sensor."""

    entity_description: SolarBillingPlanExportRateSensorEntityDescription
    _attr_native_unit_of_measurement = UNIT_USD_PER_KWH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 5

    def __init__(
        self,
        data: SolarBillingPlanExportRatesData,
        description: SolarBillingPlanExportRateSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(data, description.key)
        self.entity_description = description
        settings = data.settings
        if description.mce_only:
            self._attr_entity_registry_enabled_default = (
                settings.generation_provider == GENERATION_PROVIDER_MCE
            )
        elif not description.enabled_when_zero:
            values = data.values()
            self._attr_entity_registry_enabled_default = (
                values is not None and values.component(description.component) != 0
            )

    @property
    def available(self) -> bool:
        """Return whether rate data is available for the current hour."""
        return self.data.values() is not None

    @property
    def native_value(self) -> float | None:
        """Return the current export-rate component."""
        if (values := self.data.values()) is None:
            return None
        return decimal_to_float(values.component(self.entity_description.component))

    @property
    def extra_state_attributes(self) -> dict[str, str | float] | None:
        """Return extra state attributes."""
        if (values := self.data.values()) is None:
            return None

        next_values = self.data.next_hour_values()
        attributes: dict[str, str | float] = {
            ATTR_VINTAGE: values.vintage,
            ATTR_GENERATION_PROVIDER: values.generation_provider,
            ATTR_HOUR_START: self._local_iso(values.hour_start),
            ATTR_HOUR_END: self._local_iso(values.hour_end),
            ATTR_DATA_VERSION: values.data_version,
            ATTR_RATE_STATUS: values.rate_status,
        }
        if next_values is not None:
            attributes[ATTR_NEXT_HOUR_VALUE] = decimal_to_float(
                next_values.component(self.entity_description.component)
            )
            attributes[ATTR_NEXT_HOUR_START] = self._local_iso(next_values.hour_start)

        return attributes

    def _local_iso(self, value: datetime) -> str:
        """Return a Home Assistant-local ISO timestamp."""
        time_zone: Any = self.hass.config.time_zone
        if time_zone is None:
            return value.astimezone(UTC).isoformat()
        if isinstance(time_zone, str):
            time_zone = ZoneInfo(time_zone)
        return value.astimezone(time_zone).isoformat()

"""Base entity for Solar Billing Plan Export Rates."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import SolarBillingPlanExportRatesData


class SolarBillingPlanExportRatesEntity(Entity):
    """Base class for Solar Billing Plan Export Rates entities."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, data: SolarBillingPlanExportRatesData, key: str) -> None:
        """Initialize the entity."""
        self.data = data
        self._attr_unique_id = f"{data.entry.unique_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return self.data.device_info

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""
        await super().async_added_to_hass()
        self.async_on_remove(self.data.async_add_listener(self.async_write_ha_state))

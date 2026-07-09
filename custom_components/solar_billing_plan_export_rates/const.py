"""Constants for the Solar Billing Plan Export Rates integration."""

from typing import Final

CONF_CARE_FERA = "care_fera"
CONF_CUSTOMER_SEGMENT = "customer_segment"
CONF_ENERGY_EXPORT_BONUS = "energy_export_bonus"
CONF_GENERATION_PROVIDER = "generation_provider"
CONF_VINTAGE = "vintage"

CUSTOMER_SEGMENT_BUSINESS = "business"
CUSTOMER_SEGMENT_RESIDENTIAL = "residential"

DEFAULT_CARE_FERA = False
DEFAULT_CUSTOMER_SEGMENT = CUSTOMER_SEGMENT_RESIDENTIAL
DEFAULT_ENERGY_EXPORT_BONUS = "none"
DEFAULT_GENERATION_PROVIDER = "pge_bundled"
DEFAULT_VINTAGE = "NBT26"

DOMAIN = "solar_billing_plan_export_rates"

ENERGY_EXPORT_BONUS_LOW_INCOME = "low_income"
ENERGY_EXPORT_BONUS_NONE = "none"
ENERGY_EXPORT_BONUS_STANDARD = "standard"

GENERATION_PROVIDER_MCE: Final = "mce"
GENERATION_PROVIDER_PGE_BUNDLED: Final = "pge_bundled"

VINTAGES = ("NBT23", "NBT24", "NBT25", "NBT26", "NBT00")

UNIT_USD_PER_KWH = "USD/kWh"

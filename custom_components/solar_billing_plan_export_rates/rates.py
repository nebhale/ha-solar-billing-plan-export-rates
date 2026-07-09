"""Rate lookup and calculation for Solar Billing Plan export rates."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
import gzip
import json
from pathlib import Path
from typing import Any, Literal

from .const import (
    CUSTOMER_SEGMENT_RESIDENTIAL,
    ENERGY_EXPORT_BONUS_LOW_INCOME,
    ENERGY_EXPORT_BONUS_STANDARD,
    GENERATION_PROVIDER_MCE,
    GENERATION_PROVIDER_PGE_BUNDLED,
)

type GenerationProvider = Literal["pge_bundled", "mce"]
type RateComponent = Literal[
    "delivery",
    "generation",
    "base",
    "mce_solar_bonus",
    "energy_export_bonus",
    "care_fera",
    "all_in",
]

DATA_PATH = Path(__file__).with_name("data") / "rates.json.gz"
CARE_FERA_END_UTC = datetime(2029, 1, 1, 8, tzinfo=UTC)
MCE_SOLAR_BONUS_PERCENT = Decimal("0.10")
MONEY_QUANTUM = Decimal("0.00001")

ENERGY_EXPORT_BONUSES = {
    "NBT24": {
        ENERGY_EXPORT_BONUS_STANDARD: Decimal("0.018"),
        ENERGY_EXPORT_BONUS_LOW_INCOME: Decimal("0.072"),
    },
    "NBT25": {
        ENERGY_EXPORT_BONUS_STANDARD: Decimal("0.013"),
        ENERGY_EXPORT_BONUS_LOW_INCOME: Decimal("0.054"),
    },
    "NBT26": {
        ENERGY_EXPORT_BONUS_STANDARD: Decimal("0.009"),
        ENERGY_EXPORT_BONUS_LOW_INCOME: Decimal("0.036"),
    },
}


@dataclass(frozen=True)
class RateSettings:
    """Settings used to calculate a rate value."""

    vintage: str
    generation_provider: GenerationProvider
    customer_segment: str
    energy_export_bonus: str
    care_fera: bool


@dataclass(frozen=True)
class RateValues:
    """Calculated export-rate values for one hour."""

    vintage: str
    generation_provider: str
    hour_start: datetime
    hour_end: datetime
    delivery: Decimal
    generation: Decimal
    base: Decimal
    mce_solar_bonus: Decimal
    energy_export_bonus: Decimal
    care_fera: Decimal
    all_in: Decimal
    data_version: str
    rate_status: str

    def component(self, component: RateComponent) -> Decimal:
        """Return a component value."""
        match component:
            case "delivery":
                return self.delivery
            case "generation":
                return self.generation
            case "base":
                return self.base
            case "mce_solar_bonus":
                return self.mce_solar_bonus
            case "energy_export_bonus":
                return self.energy_export_bonus
            case "care_fera":
                return self.care_fera
            case "all_in":
                return self.all_in


class RateData:
    """Hourly export-rate lookup table."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize rate data."""
        self.data_version: str = data["data_version"]
        self.scale = Decimal(data["scale"])
        self.vintages: dict[str, dict[str, Any]] = data["vintages"]

    def calculate(self, settings: RateSettings, target: datetime) -> RateValues | None:
        """Calculate rate values for the given instant."""
        target = target.astimezone(UTC)
        if (table := self.vintages.get(settings.vintage)) is None:
            return None

        start_utc = datetime.fromisoformat(table["start_utc"])
        offset = target - start_utc
        if offset < timedelta(0):
            return None

        index = int(offset.total_seconds() // 3600)
        values = table["hourly"]
        if index >= len(values):
            return None

        delivery_raw, generation_raw = values[index]
        delivery = self._money(delivery_raw)
        generation = self._money(generation_raw)
        base = delivery + generation
        mce_solar_bonus = self._mce_solar_bonus(settings, base)
        energy_export_bonus = self._energy_export_bonus(settings)
        care_fera = self._care_fera(settings, target)
        all_in = base + mce_solar_bonus + energy_export_bonus + care_fera
        hour_start = start_utc + timedelta(hours=index)

        return RateValues(
            vintage=settings.vintage,
            generation_provider=settings.generation_provider,
            hour_start=hour_start,
            hour_end=hour_start + timedelta(hours=1) - timedelta(seconds=1),
            delivery=delivery,
            generation=generation,
            base=base,
            mce_solar_bonus=mce_solar_bonus,
            energy_export_bonus=energy_export_bonus,
            care_fera=care_fera,
            all_in=all_in,
            data_version=self.data_version,
            rate_status=self._rate_status(settings.vintage, hour_start),
        )

    def _money(self, value: int) -> Decimal:
        """Convert a scaled integer to a decimal rate."""
        return (Decimal(value) / self.scale).quantize(MONEY_QUANTUM)

    def _mce_solar_bonus(self, settings: RateSettings, base: Decimal) -> Decimal:
        """Return the MCE Solar Bonus rate."""
        if settings.generation_provider != GENERATION_PROVIDER_MCE:
            return Decimal("0.00000")
        return (base * MCE_SOLAR_BONUS_PERCENT).quantize(
            MONEY_QUANTUM, rounding=ROUND_HALF_UP
        )

    def _energy_export_bonus(self, settings: RateSettings) -> Decimal:
        """Return the Energy Export Bonus rate."""
        if (
            settings.generation_provider != GENERATION_PROVIDER_MCE
            or settings.customer_segment != CUSTOMER_SEGMENT_RESIDENTIAL
        ):
            return Decimal("0.00000")

        return ENERGY_EXPORT_BONUSES.get(settings.vintage, {}).get(
            settings.energy_export_bonus, Decimal("0.00000")
        )

    def _care_fera(self, settings: RateSettings, target: datetime) -> Decimal:
        """Return the MCE CARE/FERA export bonus rate."""
        if (
            settings.generation_provider == GENERATION_PROVIDER_MCE
            and settings.care_fera
            and target < CARE_FERA_END_UTC
        ):
            return Decimal("0.05000")
        return Decimal("0.00000")

    def _rate_status(self, vintage: str, hour_start: datetime) -> str:
        """Return a diagnostic status for the looked-up rate."""
        if vintage == "NBT00" and hour_start >= datetime(2027, 1, 1, 8, tzinfo=UTC):
            return "illustrative"
        if vintage != "NBT00":
            return "configured_vintage"
        return "actual"


def load_rate_data(path: Path = DATA_PATH) -> RateData:
    """Load vendored rate data."""
    with gzip.open(path, "rt", encoding="utf-8") as file:
        return RateData(json.load(file))


def decimal_to_float(value: Decimal) -> float:
    """Return a stable float representation for Home Assistant state values."""
    return float(value.quantize(MONEY_QUANTUM))


def default_energy_export_bonus(
    generation_provider: str, customer_segment: str, vintage: str
) -> str:
    """Return the default Energy Export Bonus option for a configuration."""
    if (
        generation_provider == GENERATION_PROVIDER_MCE
        and customer_segment == CUSTOMER_SEGMENT_RESIDENTIAL
        and vintage in ENERGY_EXPORT_BONUSES
    ):
        return ENERGY_EXPORT_BONUS_STANDARD
    return "none"


def normalize_generation_provider(value: str) -> GenerationProvider:
    """Return a typed generation provider."""
    if value == GENERATION_PROVIDER_MCE:
        return GENERATION_PROVIDER_MCE
    return GENERATION_PROVIDER_PGE_BUNDLED

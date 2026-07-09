"""Tests for Solar Billing Plan rate calculations."""

from datetime import UTC, datetime
from decimal import Decimal

from custom_components.solar_billing_plan_export_rates.const import (
    CUSTOMER_SEGMENT_RESIDENTIAL,
    ENERGY_EXPORT_BONUS_NONE,
    ENERGY_EXPORT_BONUS_STANDARD,
    GENERATION_PROVIDER_MCE,
    GENERATION_PROVIDER_PGE_BUNDLED,
)
from custom_components.solar_billing_plan_export_rates.rates import (
    RateSettings,
    default_energy_export_bonus,
    load_rate_data,
)


def test_nbt25_base_values() -> None:
    """Test known NBT25 base values."""
    rate_data = load_rate_data()
    settings = RateSettings(
        vintage="NBT25",
        generation_provider=GENERATION_PROVIDER_PGE_BUNDLED,
        customer_segment=CUSTOMER_SEGMENT_RESIDENTIAL,
        energy_export_bonus=ENERGY_EXPORT_BONUS_NONE,
        care_fera=False,
    )

    first = rate_data.calculate(settings, datetime(2026, 7, 9, 1, 52, tzinfo=UTC))
    assert first is not None
    assert first.delivery == Decimal("0.26840")
    assert first.generation == Decimal("0.09593")
    assert first.base == Decimal("0.36433")
    assert first.all_in == Decimal("0.36433")

    second = rate_data.calculate(settings, datetime(2026, 7, 9, 3, 52, tzinfo=UTC))
    assert second is not None
    assert second.delivery == Decimal("0.17324")
    assert second.generation == Decimal("0.09096")
    assert second.base == Decimal("0.26420")
    assert second.all_in == Decimal("0.26420")


def test_nbt25_mce_standard_without_care_fera() -> None:
    """Test known NBT25 MCE standard calculations without CARE/FERA."""
    rate_data = load_rate_data()
    settings = RateSettings(
        vintage="NBT25",
        generation_provider=GENERATION_PROVIDER_MCE,
        customer_segment=CUSTOMER_SEGMENT_RESIDENTIAL,
        energy_export_bonus=ENERGY_EXPORT_BONUS_STANDARD,
        care_fera=False,
    )

    previous = rate_data.calculate(settings, datetime(2026, 7, 9, 0, 56, tzinfo=UTC))
    assert previous is not None
    assert previous.delivery == Decimal("0.25932")
    assert previous.generation == Decimal("0.06615")
    assert previous.base == Decimal("0.32547")
    assert previous.mce_solar_bonus == Decimal("0.03255")
    assert previous.energy_export_bonus == Decimal("0.013")
    assert previous.care_fera == Decimal("0.00000")
    assert previous.all_in == Decimal("0.37102")

    current = rate_data.calculate(settings, datetime(2026, 7, 9, 1, 52, tzinfo=UTC))
    assert current is not None
    assert current.mce_solar_bonus == Decimal("0.03643")
    assert current.energy_export_bonus == Decimal("0.013")
    assert current.care_fera == Decimal("0.00000")
    assert current.all_in == Decimal("0.41376")

    future = rate_data.calculate(settings, datetime(2026, 7, 9, 3, 52, tzinfo=UTC))
    assert future is not None
    assert future.mce_solar_bonus == Decimal("0.02642")
    assert future.energy_export_bonus == Decimal("0.013")
    assert future.care_fera == Decimal("0.00000")
    assert future.all_in == Decimal("0.30362")


def test_care_fera_cutoff() -> None:
    """Test CARE/FERA is only applied before its cutoff."""
    rate_data = load_rate_data()
    settings = RateSettings(
        vintage="NBT25",
        generation_provider=GENERATION_PROVIDER_MCE,
        customer_segment=CUSTOMER_SEGMENT_RESIDENTIAL,
        energy_export_bonus=ENERGY_EXPORT_BONUS_NONE,
        care_fera=True,
    )

    active = rate_data.calculate(settings, datetime(2028, 12, 31, 7, 59, tzinfo=UTC))
    assert active is not None
    assert active.care_fera == Decimal("0.05000")

    expired = rate_data.calculate(settings, datetime(2029, 1, 1, 8, tzinfo=UTC))
    assert expired is not None
    assert expired.care_fera == Decimal("0.00000")


def test_default_energy_export_bonus() -> None:
    """Test default Energy Export Bonus selection."""
    assert (
        default_energy_export_bonus(
            GENERATION_PROVIDER_MCE, CUSTOMER_SEGMENT_RESIDENTIAL, "NBT26"
        )
        == ENERGY_EXPORT_BONUS_STANDARD
    )
    assert (
        default_energy_export_bonus(
            GENERATION_PROVIDER_PGE_BUNDLED, CUSTOMER_SEGMENT_RESIDENTIAL, "NBT26"
        )
        == ENERGY_EXPORT_BONUS_NONE
    )


def test_out_of_range_returns_none() -> None:
    """Test out-of-range lookups return None."""
    rate_data = load_rate_data()
    settings = RateSettings(
        vintage="NBT26",
        generation_provider=GENERATION_PROVIDER_PGE_BUNDLED,
        customer_segment=CUSTOMER_SEGMENT_RESIDENTIAL,
        energy_export_bonus=ENERGY_EXPORT_BONUS_NONE,
        care_fera=False,
    )

    assert rate_data.calculate(settings, datetime(2025, 12, 31, 7, tzinfo=UTC)) is None

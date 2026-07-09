#!/usr/bin/env python3
"""Generate compact Solar Billing Plan export-rate data from PG&E CSV files."""

import argparse
from collections import defaultdict
import csv
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import gzip
import json
from pathlib import Path
from typing import Any

SCALE = 100000
DATA_VERSION = "PGE-SBP-Export-Rates-2026-07"
CSV_FILES = {
    "NBT23": "PG&E NBT EEC Values 2023 Vintage.csv",
    "NBT24": "PG&E NBT EEC Values 2024 Vintage.csv",
    "NBT25": "PG&E NBT EEC Values 2025 Vintage.csv",
    "NBT26": "PG&E NBT EEC Values 2026 Vintage.csv",
    "NBT00": "PG&E NBT EEC Values Floating Vintage.csv",
}


def parse_datetime(date_value: str, time_value: str) -> datetime:
    """Parse a PG&E UTC date/time pair."""
    return datetime.strptime(f"{date_value} {time_value}", "%m/%d/%Y %H:%M:%S").replace(
        tzinfo=UTC
    )


def component_from_rin(rin: str) -> int:
    """Return the component index for a PG&E RIN."""
    if "USCA-PGXX" in rin:
        return 0
    if "USCA-XXPG" in rin:
        return 1
    raise ValueError(f"Unknown rate component in RIN {rin}")


def scaled_value(value: str) -> int:
    """Return a scaled integer rate value."""
    decimal_value = Decimal(value)
    if max(0, -decimal_value.as_tuple().exponent) > 5:
        raise ValueError(f"Value has more than five decimal places: {value}")
    return int(decimal_value * SCALE)


def read_vintage(path: Path, expected_vintage: str) -> dict[str, Any]:
    """Read and validate one vintage CSV."""
    by_start: dict[datetime, list[int | None]] = defaultdict(lambda: [None, None])

    with path.open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            if row["RateName"] != expected_vintage:
                raise ValueError(
                    f"Expected {expected_vintage}, got {row['RateName']} in {path}"
                )
            start = parse_datetime(row["DateStart"], row["TimeStart"])
            end = parse_datetime(row["DateEnd"], row["TimeEnd"])
            if end - start != timedelta(minutes=59, seconds=59):
                raise ValueError(f"Unexpected interval {start} - {end} in {path}")
            by_start[start][component_from_rin(row["RIN"])] = scaled_value(row["Value"])

    ordered_starts = sorted(by_start)
    if not ordered_starts:
        raise ValueError(f"No rows found in {path}")

    hourly: list[list[int]] = []
    expected_start = ordered_starts[0]
    for start in ordered_starts:
        if start != expected_start:
            raise ValueError(f"Gap in {path}: expected {expected_start}, got {start}")
        delivery, generation = by_start[start]
        if delivery is None or generation is None:
            raise ValueError(f"Missing component for {start} in {path}")
        hourly.append([delivery, generation])
        expected_start += timedelta(hours=1)

    return {
        "start_utc": ordered_starts[0].isoformat(),
        "end_utc": (ordered_starts[-1] + timedelta(minutes=59, seconds=59)).isoformat(),
        "hourly": hourly,
    }


def build_data(source: Path) -> dict[str, Any]:
    """Build compact rate data."""
    return {
        "data_version": DATA_VERSION,
        "scale": SCALE,
        "vintages": {
            vintage: read_vintage(source / filename, vintage)
            for vintage, filename in CSV_FILES.items()
        },
    }


def write_data(data: dict[str, Any], destination: Path) -> None:
    """Write deterministic gzipped JSON."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
    with (
        destination.open("wb") as output,
        gzip.GzipFile(
            filename="", mode="wb", fileobj=output, compresslevel=9, mtime=0
        ) as gzip_file,
    ):
        gzip_file.write(raw)


def main() -> None:
    """Run the data generator."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path(
            "custom_components/solar_billing_plan_export_rates/data/rates.json.gz"
        ),
    )
    args = parser.parse_args()

    write_data(build_data(args.source), args.destination)

    with gzip.open(args.destination, "rb") as file:
        size = len(file.read())
    compressed_size = args.destination.stat().st_size
    print(
        f"Wrote {args.destination} ({compressed_size} compressed bytes, "
        f"{size} uncompressed bytes)"
    )


if __name__ == "__main__":
    main()

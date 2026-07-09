# Solar Billing Plan Export Rates for Home Assistant

Solar Billing Plan Export Rates is a custom Home Assistant integration for
exposing PG&E Solar Billing Plan export credit rates as sensors.

The integration vendors compact hourly export-rate data generated from PG&E's
published Solar Billing Plan export-rate CSV files. It can calculate PG&E
bundled values or Marin Clean Energy values with MCE's Solar Bonus and optional
eligible export bonus credits.

## Installation

### HACS

1. Add this repository to HACS as a custom repository.
2. Select `Integration` as the repository type.
3. Install `Solar Billing Plan Export Rates`.
4. Restart Home Assistant.
5. Add the integration from **Settings > Devices & services**.

### Manual

Copy `custom_components/solar_billing_plan_export_rates` into your Home
Assistant `custom_components` directory and restart Home Assistant.

## Configuration

The default setup uses `NBT26` and `PG&E Bundled`. The config flow also supports
Marin Clean Energy and the published NBT vintages `NBT23`, `NBT24`, `NBT25`,
`NBT26`, and `NBT00`.

The integration exposes component sensors and an all-in export-rate sensor.
Annual cash-out, net surplus compensation settlement, and storage credits are
outside this integration's scope.

## Development

This repository follows the HACS custom integration layout:

```text
custom_components/solar_billing_plan_export_rates/
  __init__.py
  config_flow.py
  const.py
  manifest.json
  sensor.py
```

Generate the compact rate table from PG&E CSV files:

```bash
python scripts/generate_rates.py /path/to/PGE-Solar-Billing-Plan-Export-Rates
```

Run validation:

```bash
uv sync --group lint --group test --no-install-project
uv run --no-sync pytest tests
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pylint custom_components tests
uv run --no-sync mypy
```

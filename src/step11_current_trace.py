"""Write the Step 11 current-state trace from the real Step 10 observation."""

from __future__ import annotations

import json
from pathlib import Path

from .forecast_engine_v2 import ForecastEngineV2

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports" / "step10_forecast_trace.json"
JSON_OUT = ROOT / "reports" / "step11_forecast_trace.json"
MD_OUT = ROOT / "reports" / "step11_forecast_trace.md"


def main() -> dict:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    observation = {"Date": source["reference_date"], **source["features"]}
    result = ForecastEngineV2(ROOT).predict(observation)
    trace = {
        "source_trace": str(SOURCE.relative_to(ROOT)),
        "reference_date": source["reference_date"],
        "data_as_of": source["data_as_of"],
        "district": source["district"],
        "block": source["block"],
        "panchayat": source["panchayat"],
        "panchayat_id": source["panchayat_id"],
        "features": source["features"],
        "v2_forecast": result,
    }
    JSON_OUT.write_text(json.dumps(trace, indent=2, allow_nan=False), encoding="utf-8")

    lines = [
        "# Step 11 Current 2026 V2 Forecast Trace",
        "",
        "This trace uses the real current observation already recorded by Step 10; it does not generate a synthetic input or replace missing fields with zero/default weather.",
        "",
        "## Selected location",
        "",
        f"- Panchayat: {source['panchayat']} (`{source['panchayat_id']}`)",
        f"- Block: {source['block']}",
        f"- District: {source['district']}",
        f"- Reference date / data as of: `{source['reference_date']}` / `{source['data_as_of']}`",
        "",
        "## Current features",
        "",
        "| Feature | Value |",
        "|---|---:|",
    ]
    for name, value in source["features"].items():
        if name != "atmospheric_fields":
            lines.append(f"| `{name}` | {value} |")
    lines.extend([
        "",
        "## V2 current forecast trace",
        "",
        f"- Engine: `{result['engine_version']}`",
        f"- Short-horizon status: `{result['operational_status']}`",
        "",
        "| Event | Applicability | Probability | Model status |",
        "|---|---|---:|---|",
    ])
    for event, value in result["events"].items():
        probability = "unavailable" if value["probability"] is None else f"{value['probability']:.6f}"
        lines.append(f"| {event} | `{value['applicability']}` | {probability} | `{value['model_status']}` |")
    lines.extend([
        "",
        "## Statistical 7–30 day outlook",
        "",
        f"- Status: `{result['statistical_7_30_day_outlook']['forecast_status']}`",
        f"- Disclaimer: {result['statistical_7_30_day_outlook']['disclaimer']}",
        "",
        "| Period | Event | Applicability | Probability |",
        "|---|---|---|---:|",
    ])
    for period, events in result["statistical_7_30_day_outlook"]["horizons"].items():
        for event, value in events.items():
            probability = "unavailable" if value["probability"] is None else f"{value['probability']:.6f}"
            lines.append(f"| {period} | {event} | `{value['applicability']}` | {probability} |")
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "`UNAVAILABLE` and `OUT_OF_SEASON` are preserved as explicit states. No missing atmospheric field is converted to zero, and no V2 probability is promoted as a backend production response by this trace alone.",
        "",
        f"Machine-readable copy: [{JSON_OUT.name}]({JSON_OUT.name})",
    ])
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return trace


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, allow_nan=False))

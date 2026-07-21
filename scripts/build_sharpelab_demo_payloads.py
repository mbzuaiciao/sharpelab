#!/usr/bin/env python3
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportMissingImports=false
"""Build and validate deterministic SharpeLab demonstration JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from sharpelab.adapter import SCENARIO_BUILDERS, build_sharpelab_payload


def build_payloads(output_dir: Path | None = None) -> tuple[Path, ...]:
    """Generate and write SharpeLab demo payload JSON files for scenarios."""
    root = Path(__file__).resolve().parents[1]
    target_dir = output_dir or (root / "demo/sharpelab")
    target_dir.mkdir(parents=True, exist_ok=True)

    output_paths: list[Path] = []

    for scenario_id in SCENARIO_BUILDERS:
        payload = build_sharpelab_payload(scenario_id, config_root=root / "configs")
        output_path = target_dir / f"{scenario_id}.json"

        data_dict = payload.model_dump(mode="json")
        formatted_json = json.dumps(data_dict, indent=2, sort_keys=True)
        output_path.write_text(formatted_json + "\n", encoding="utf-8")
        print(f"Wrote SharpeLab demo payload to: {output_path}")
        output_paths.append(output_path)

    return tuple(output_paths)


def main() -> int:
    build_payloads()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

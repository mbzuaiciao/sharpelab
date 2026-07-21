"""Integration tests for SharpeLab demo payload generation across all 3 scenarios."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_sharpelab_demo_payloads import build_payloads

from sharpelab.adapter import SCENARIO_BUILDERS, build_sharpelab_payload


def test_build_sharpelab_demo_payload_all_scenarios_reproducibility(
    tmp_path: Path,
) -> None:
    output_files_1 = build_payloads(output_dir=tmp_path / "run1")
    output_files_2 = build_payloads(output_dir=tmp_path / "run2")

    assert len(output_files_1) == 3
    assert len(output_files_2) == 3

    for f1, f2 in zip(output_files_1, output_files_2, strict=True):
        content_1 = f1.read_text(encoding="utf-8")
        content_2 = f2.read_text(encoding="utf-8")
        assert content_1 == content_2, f"Payload mismatch for {f1.name}"

        data = json.loads(content_1)
        scenario_id = data["scenario_id"]
        assert scenario_id in SCENARIO_BUILDERS

        direct_payload = build_sharpelab_payload(scenario_id)
        assert data["verdict"] == direct_payload.verdict
        assert data["seed"] == direct_payload.seed
        assert data["sample_size"] == direct_payload.sample_size

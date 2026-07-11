from __future__ import annotations

import html
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from tests.quality.dynamic.models import DynamicConcept, DynamicScenario

CAMPAIGN_SCHEMA_VERSION = 1


def derive_campaign_seeds(base_seed: int, runs: int) -> list[int]:
    if runs <= 0:
        raise ValueError("--runs must be greater than zero.")

    seeds = [base_seed]
    rng = random.Random(base_seed)

    while len(seeds) < runs:
        candidate = rng.randrange(0, 2**32)

        if candidate not in seeds:
            seeds.append(candidate)

    return seeds


def resolve_campaign_seeds(
    *,
    explicit_seeds: Iterable[int] = (),
    base_seed: int,
    runs: int,
) -> list[int]:
    seeds = list(explicit_seeds)

    if not seeds:
        return derive_campaign_seeds(base_seed, runs)

    if len(set(seeds)) != len(seeds):
        raise ValueError("Explicit --seed values must be unique.")

    return seeds


def expected_template_keys(
    concepts: Iterable[DynamicConcept],
) -> set[str]:
    return {
        f"{concept.id}:{template.id}"
        for concept in concepts
        for template in concept.templates
    }


def aggregate_coverage(
    scenarios: Iterable[DynamicScenario],
    *,
    concepts: Iterable[DynamicConcept],
) -> dict[str, Any]:
    scenario_list = list(scenarios)
    concept_counts = Counter(scenario.concept_id for scenario in scenario_list)
    template_counts = Counter(
        f"{scenario.concept_id}:{scenario.template_id}"
        for scenario in scenario_list
    )
    source_counts = Counter(scenario.source_kind for scenario in scenario_list)
    legal_format_counts = Counter(
        format_name
        for scenario in scenario_list
        for format_name in scenario.card_legal_formats
    )
    set_counts = Counter(
        scenario.card_set_name
        for scenario in scenario_list
        if scenario.card_set_name
    )
    cards = sorted(
        {
            scenario.card_name
            for scenario in scenario_list
            if scenario.card_name
        }
    )
    selected_concepts = [concept.id for concept in concepts]
    expected_templates = expected_template_keys(concepts)
    seen_templates = set(template_counts)

    return {
        "selected_concepts": selected_concepts,
        "concept_counts": dict(sorted(concept_counts.items())),
        "missing_concepts": sorted(set(selected_concepts) - set(concept_counts)),
        "template_counts": dict(sorted(template_counts.items())),
        "templates_seen": len(seen_templates),
        "templates_expected": len(expected_templates),
        "missing_templates": sorted(expected_templates - seen_templates),
        "complete": (
            not (set(selected_concepts) - set(concept_counts))
            and not (expected_templates - seen_templates)
        ),
        "source_kind_counts": dict(sorted(source_counts.items())),
        "unique_cards": len(cards),
        "card_names": cards,
        "legal_format_counts": dict(sorted(legal_format_counts.items())),
        "set_counts": dict(sorted(set_counts.items())),
    }


def campaign_status(*, failures: int, warnings: int) -> str:
    if failures:
        return "FAIL"

    if warnings:
        return "WARN"

    return "PASS"


def build_campaign_payload(
    *,
    base_seed: int,
    seeds: list[int],
    cases_per_seed: int,
    run_summaries: list[dict[str, Any]],
    scenarios: list[DynamicScenario],
    concepts: list[DynamicConcept],
    total_elapsed: float,
) -> dict[str, Any]:
    failures = sum(run["failures"] for run in run_summaries)
    warnings = sum(run["warnings"] for run in run_summaries)
    cases_executed = sum(run["cases"] for run in run_summaries)

    return {
        "schema_version": CAMPAIGN_SCHEMA_VERSION,
        "base_seed": base_seed,
        "seeds": seeds,
        "runs_requested": len(seeds),
        "runs_executed": len(run_summaries),
        "cases_per_seed": cases_per_seed,
        "cases_executed": cases_executed,
        "failures": failures,
        "warnings": warnings,
        "status": campaign_status(failures=failures, warnings=warnings),
        "elapsed_seconds": round(total_elapsed, 6),
        "coverage": aggregate_coverage(scenarios, concepts=concepts),
        "runs": run_summaries,
    }


def write_campaign_summary(
    output_dir: str | Path,
    payload: dict[str, Any],
) -> dict[str, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "campaign_summary.json"
    txt_path = directory / "campaign_summary.txt"
    html_path = directory / "campaign_summary.html"

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    txt_path.write_text(_render_txt(payload), encoding="utf-8")
    html_path.write_text(_render_html(payload), encoding="utf-8")

    return {"json": json_path, "txt": txt_path, "html": html_path}


def _render_txt(payload: dict[str, Any]) -> str:
    coverage = payload["coverage"]
    lines = [
        "=" * 80,
        "MagicAI Dynamic Campaign",
        "=" * 80,
        "",
        f"Base seed        : {payload['base_seed']}",
        f"Seeds            : {', '.join(str(seed) for seed in payload['seeds'])}",
        f"Runs             : {payload['runs_executed']}/{payload['runs_requested']}",
        f"Cases per seed   : {payload['cases_per_seed']}",
        f"Cases executed   : {payload['cases_executed']}",
        f"Failures         : {payload['failures']}",
        f"Warnings         : {payload['warnings']}",
        f"Time             : {payload['elapsed_seconds']:.2f}s",
        f"Status           : {payload['status']}",
        "",
        "COVERAGE",
        "-" * 80,
        (
            "Concepts         : "
            f"{len(coverage['concept_counts'])}/"
            f"{len(coverage['selected_concepts'])}"
        ),
        (
            "Templates        : "
            f"{coverage['templates_seen']}/"
            f"{coverage['templates_expected']}"
        ),
        f"Unique cards     : {coverage['unique_cards']}",
        (
            "Legal formats    : "
            + ", ".join(
                f"{format_name}={count}"
                for format_name, count
                in coverage["legal_format_counts"].items()
            )
        ),
        (
            "Source kinds     : "
            + ", ".join(
                f"{kind}={count}"
                for kind, count in coverage["source_kind_counts"].items()
            )
        ),
    ]

    if coverage["missing_concepts"]:
        lines.append(
            "Missing concepts : " + ", ".join(coverage["missing_concepts"])
        )

    if coverage["missing_templates"]:
        lines.append(
            "Missing templates: " + ", ".join(coverage["missing_templates"])
        )

    lines.extend(["", "RUNS", "-" * 80])

    for run in payload["runs"]:
        lines.append(
            f"#{run['index']:02d} seed={run['seed']} "
            f"cases={run['cases']} failures={run['failures']} "
            f"warnings={run['warnings']} status={run['status']} "
            f"time={run['elapsed_seconds']:.2f}s"
        )

    return "\n".join(lines) + "\n"


def _render_html(payload: dict[str, Any]) -> str:
    coverage = payload["coverage"]
    status_class = payload["status"].lower()
    rows = []

    for run in payload["runs"]:
        rows.append(
            "<tr>"
            f"<td>{run['index']}</td>"
            f"<td>{run['seed']}</td>"
            f"<td>{run['cases']}</td>"
            f"<td>{run['failures']}</td>"
            f"<td>{run['warnings']}</td>"
            f"<td><span class='badge {run['status'].lower()}'>"
            f"{html.escape(run['status'])}</span></td>"
            f"<td>{run['elapsed_seconds']:.2f}s</td>"
            f"<td><a href='{html.escape(run['html'])}'>report</a></td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MagicAI Dynamic Campaign</title>
  <style>
    :root {{ color-scheme: light dark; --bg:#111827; --panel:#1f2937;
      --text:#e5e7eb; --muted:#9ca3af; --border:#374151;
      --pass:#22c55e; --warn:#f59e0b; --fail:#ef4444; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text);
      font-family:Inter,system-ui,sans-serif; }}
    main {{ width:min(1150px,calc(100% - 32px)); margin:32px auto; }}
    header {{ display:flex; justify-content:space-between; gap:16px; }}
    .badge {{ padding:5px 10px; border-radius:999px; font-weight:800;
      border:1px solid var(--border); }}
    .pass {{ color:var(--pass); }} .warn {{ color:var(--warn); }}
    .fail {{ color:var(--fail); }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
      gap:12px; margin:22px 0; }}
    .metric {{ background:var(--panel); border:1px solid var(--border);
      border-radius:16px; padding:16px; }}
    .metric strong {{ display:block; font-size:1.55rem; }}
    .metric span {{ color:var(--muted); }}
    table {{ width:100%; border-collapse:collapse; background:var(--panel);
      border:1px solid var(--border); }}
    th,td {{ padding:11px 13px; border-bottom:1px solid var(--border);
      text-align:left; }}
    th {{ color:var(--muted); }} a {{ color:#60a5fa; }}
  </style>
</head>
<body><main>
<header><div><h1>MagicAI Dynamic Campaign</h1>
<p>Campaña multisemilla reproducible y cobertura acumulada.</p></div>
<span class="badge {status_class}">{html.escape(payload['status'])}</span></header>
<section class="metrics">
<div class="metric"><strong>{payload['runs_executed']}/{payload['runs_requested']}</strong><span>Ejecuciones</span></div>
<div class="metric"><strong>{payload['cases_executed']}</strong><span>Casos</span></div>
<div class="metric"><strong>{payload['failures']}</strong><span>Fallos</span></div>
<div class="metric"><strong>{payload['warnings']}</strong><span>Warnings</span></div>
<div class="metric"><strong>{coverage['templates_seen']}/{coverage['templates_expected']}</strong><span>Plantillas</span></div>
<div class="metric"><strong>{coverage['unique_cards']}</strong><span>Cartas únicas</span></div>
<div class="metric"><strong>{payload['elapsed_seconds']:.1f}s</strong><span>Tiempo</span></div>
</section>
<table><thead><tr><th>#</th><th>Seed</th><th>Casos</th><th>FAIL</th>
<th>WARN</th><th>Estado</th><th>Tiempo</th><th>Informe</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</main></body></html>"""

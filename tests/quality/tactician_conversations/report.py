from __future__ import annotations

import html
import json
from pathlib import Path


def write_reports(results: dict, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "summary.json"
    html_path = output / "report.html"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(_render_html(results), encoding="utf-8")
    return json_path, html_path


def _render_html(results: dict) -> str:
    rows: list[str] = []
    for scenario in results.get("scenarios", []):
        for turn in scenario.get("turns", []):
            failures = "<br>".join(html.escape(item) for item in turn.get("failures", [])) or "—"
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(scenario.get('id', '')))}</td>"
                f"<td>{turn.get('turn', '')}</td>"
                f"<td>{html.escape(str(turn.get('question', '')))}</td>"
                f"<td>{'PASS' if turn.get('passed') else 'FAIL'}</td>"
                f"<td>{failures}</td>"
                "</tr>"
            )
    return """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>MagicAI Tactician Conversation Gauntlet</title>
<style>
body{font-family:system-ui,sans-serif;margin:2rem;line-height:1.4}table{border-collapse:collapse;width:100%%}
th,td{border:1px solid #ccc;padding:.55rem;vertical-align:top}th{background:#f3f3f3;text-align:left}
</style></head>
<body>
<h1>MagicAI Tactician Conversation Gauntlet</h1>
<p>Scenarios: %s · Turns: %s · Passed: %s · Failed: %s</p>
<table><thead><tr><th>Scenario</th><th>Turn</th><th>Question</th><th>Result</th><th>Failures</th></tr></thead>
<tbody>%s</tbody></table>
</body></html>""" % (
        results.get("scenario_count", 0),
        results.get("turn_count", 0),
        results.get("passed_turns", 0),
        results.get("failed_turns", 0),
        "".join(rows),
    )

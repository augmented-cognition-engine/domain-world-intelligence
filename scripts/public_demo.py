#!/usr/bin/env python3
"""Generate the public, reproducible World Intelligence proof surface.

The demo is a presentation layer over the accepted P2B harnesses.  It does not
implement intelligence behavior, reinterpret the frozen packet, or call a live
source.  The command fails if any release-critical identity or impact count
drifts from the accepted contracts.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
from collections.abc import Sequence
from pathlib import Path
from string import Template
from typing import Any

try:
    from scripts.p2b_independent_case_brief import (
        HYDROLOGY_ROOT,
        LEDGER_ROOT,
        LEDGER_SYNDICATION,
        run_independent_case_brief,
    )
    from scripts.p2b_supersession_impact import (
        _build_world,
        run_supersession_impact,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by users without ACE
    if exc.name == "ace" or (exc.name and exc.name.startswith("ace.")):
        raise SystemExit(
            "ACE Core + Intelligence is required. Install ace-core or add its checkout "
            "to PYTHONPATH before running this prepared demo."
        ) from exc
    raise


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "public-demo"

LEDGER_SUPERSESSION = "supersession:correction_114_over_report_1088"
EXPECTED = {
    "scenario_id": "meridia_reservoir_release_72h",
    "case_id": "case:412426eee708d56f6bda931ccf9e5d8b",
    "brief_id": "brief:25d8232c9bfa27050bdcb160fb75f06c",
    "status_projection_id": ("brief_derivation_family_status_projection:3500889a2d75af7a5484a681afbee34c"),
    "impact_projection_id": ("supersession_impact_projection:f3723de8e9ac5c4390c5c46137f3765e"),
    "impacted_resources": 11,
    "impacted_claims": 9,
    "direct": 6,
    "transitive": 5,
    "unaffected": 16,
    "max_depth": 3,
}

SECTION_TITLES = (
    "What happened",
    "What changed",
    "Established records",
    "Attributed claims",
    "Where sources agree",
    "Where sources conflict",
    "ACE inferences",
    "Unknowns",
    "Why it matters",
    "Watchpoints",
    "Limitations",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _assert_release_contract(data: dict[str, Any]) -> None:
    """Fail visibly instead of publishing a demo over silently drifted facts."""

    actual = {
        "scenario_id": data["scenario"]["id"],
        **data["identities"],
        "impacted_resources": data["correction_impact"]["impacted_resources"],
        "impacted_claims": data["correction_impact"]["impacted_claims"],
        "direct": data["correction_impact"]["direct"],
        "transitive": data["correction_impact"]["transitive"],
        "unaffected": data["correction_impact"]["unaffected"],
        "max_depth": data["correction_impact"]["max_depth"],
    }
    if actual != EXPECTED:
        raise RuntimeError(
            "Public demo contract drifted from the accepted release proof:\n"
            f"expected={_canonical_json(EXPECTED)}actual={_canonical_json(actual)}"
        )


async def collect_demo_data() -> dict[str, Any]:
    """Run the accepted harnesses and shape their exact outputs for presentation."""

    independent, impact, world = await asyncio.gather(
        run_independent_case_brief(),
        run_supersession_impact(),
        _build_world(),
    )
    admission = world["admission"]
    brief = admission.brief
    status_projection = admission.status_projection
    status_by_claim = {str(item.claim_id): item for item in status_projection.claim_statuses}
    citation_sources = {str(item.citation_id): str(item.source_ref) for item in brief.citations}

    claims: list[dict[str, Any]] = []
    for section, claim in zip(SECTION_TITLES, brief.claims, strict=True):
        status = status_by_claim[str(claim.claim_id)]
        claims.append(
            {
                "section": section,
                "claim_id": str(claim.claim_id),
                "statement": claim.statement,
                "status": status.status_id,
                "grounding_kind": claim.grounding_kind.value,
                "confidence": claim.confidence,
                "cited_sources": [citation_sources[str(citation_id)] for citation_id in claim.citation_ids],
                "support_record_ids": list(status.support_record_ids),
                "distinct_derivation_families": status.distinct_derivation_family_count,
                "required_derivation_families": status.required_distinct_derivation_families,
                "carries_uncertainty": status.carries_uncertainty,
            }
        )

    observation_ids = world["observation_ids"]
    ledger = impact["supersessions"][LEDGER_SUPERSESSION]
    data = {
        "contract": "ace.world-intelligence.public-demo/v1alpha1",
        "release": "0.7.0-rc1",
        "scenario": {
            "id": independent["scenario_id"],
            "mode": "PREPARED",
            "state": "FROZEN",
            "kind": "synthetic, hermetic, redistributable fixture",
            "is_live": False,
            "generated_at": brief.generated_at.isoformat().replace("+00:00", "Z"),
            "as_of": brief.as_of.isoformat().replace("+00:00", "Z"),
        },
        "identities": {
            "case_id": independent["case"]["case_id"],
            "brief_id": independent["brief"]["brief_id"],
            "status_projection_id": independent["status_projection"]["projection_id"],
            "impact_projection_id": ledger["projection_id"],
        },
        "evidence_graph": {
            "policy": independent["status_projection"]["derivation_family_policy"],
            "displayed_record_count": 4,
            "displayed_derivation_root_count": 2,
            "ledger_family": {
                "root": {
                    "source_ref": LEDGER_ROOT,
                    "resource_id": observation_ids[LEDGER_ROOT],
                    "label": "Ledger report 1088",
                },
                "derived_records": [
                    {
                        "source_ref": source_ref,
                        "resource_id": observation_ids[source_ref],
                        "label": label,
                    }
                    for source_ref, label in zip(
                        LEDGER_SYNDICATION,
                        ("Coastal Wire syndication", "Harborview reprint"),
                        strict=True,
                    )
                ],
            },
            "independent_family": {
                "root": {
                    "source_ref": HYDROLOGY_ROOT,
                    "resource_id": observation_ids[HYDROLOGY_ROOT],
                    "label": "Basin gauge series W10",
                }
            },
            "corroboration": {
                "claim_id": next(item["claim_id"] for item in claims if item["status"] == "corroborated"),
                "required_distinct_roots": 2,
                "observed_distinct_roots": 2,
                "publisher_count_is_independence": False,
            },
        },
        "brief": {
            "title": brief.title,
            "claim_count": len(claims),
            "citation_count": len(brief.citations),
            "claims": claims,
            "claims_per_status": independent["status_projection"]["claims_per_status"],
        },
        "correction_impact": {
            "supersession_id": LEDGER_SUPERSESSION,
            "superseded_resource_id": ledger["superseded_resource_id"],
            "superseder_resource_id": ledger["superseder_resource_id"],
            "impacted_resources": ledger["impacted_count"],
            "impacted_claims": ledger["impacted_claim_count"],
            "fully_impacted_claims": ledger["fully_impacted_claim_count"],
            "partially_impacted_claims": ledger["partially_impacted_claim_count"],
            "direct": ledger["direct_count"],
            "transitive": ledger["transitive_count"],
            "unaffected": ledger["unaffected_count"],
            "max_depth": ledger["max_depth"],
            "closure_size": ledger["closure_size"],
            "impact_means_dependency_not_falsehood": impact["proven"]["impact_is_dependency_not_falsehood"],
        },
        "historical_integrity": impact["historical_integrity"],
        "governance": {
            "all_contract_requests_closed": impact["closed_requests"],
            "runtime_gaps": impact["runtime_gaps"],
            "deterministic_brief_replay": independent["governance"]["deterministic_replay"],
            "impact_replay_exact": ledger["durable_replay_is_exact"],
            "live_resources": impact["invariants"]["live_resources"],
            "external_action": impact["invariants"]["external_action"],
        },
        "limits": [
            "Prepared synthetic scenario; no LIVE source adapter is exercised.",
            "Independence is only as strong as the admitted lineage.",
            "Impact identifies dependency, not truth or falsehood.",
            "Developer-preview release candidate; no production-scale claim.",
        ],
    }
    _assert_release_contract(data)
    return data


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _short(value: str, head: int = 18, tail: int = 8) -> str:
    if len(value) <= head + tail + 1:
        return value
    return f"{value[:head]}…{value[-tail:]}"


def _claim_rows(data: dict[str, Any]) -> str:
    chosen_sections = {
        "What happened",
        "Attributed claims",
        "Where sources agree",
        "Where sources conflict",
        "Watchpoints",
    }
    rows: list[str] = []
    for claim in data["brief"]["claims"]:
        if claim["section"] not in chosen_sections:
            continue
        sources = claim["cited_sources"] or claim["support_record_ids"]
        source_text = " · ".join(_short(item, 24, 6) for item in sources[:2])
        status_class = {
            "corroborated": "verified",
            "attributed_claim": "attributed",
            "disputed": "uncertain",
            "scenario": "uncertain",
        }.get(claim["status"], "neutral")
        rows.append(
            '<article class="claim-row">'
            f'<div><span class="status {status_class}">{_e(claim["status"].replace("_", " "))}</span>'
            f'<span class="section-label">{_e(claim["section"])}</span></div>'
            f"<p>{_e(claim['statement'])}</p>"
            f'<code title="{_e(" | ".join(sources))}">{_e(source_text)}</code>'
            "</article>"
        )
    return "".join(rows)


def _identity_rows(data: dict[str, Any]) -> str:
    labels = (
        ("CASE", "case_id"),
        ("BRIEF", "brief_id"),
        ("FAMILY", "status_projection_id"),
        ("IMPACT", "impact_projection_id"),
    )
    return "".join(
        f'<div class="identity"><span>{label}</span>'
        f'<code title="{_e(data["identities"][key])}">{_e(_short(data["identities"][key], 22, 9))}</code></div>'
        for label, key in labels
    )


_HTML = Template(
    """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>ACE World Intelligence — Reality Brief</title>
<style>
:root{--bg:#080b0b;--panel:#101414;--raised:#151a19;--line:#29312f;--text:#f4f6f3;--muted:#97a09c;--dim:#68716d;--mint:#79f2bd;--amber:#f0bd62;--coral:#ff756d;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;--sans:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text);font-family:var(--sans)}body{padding:0 24px 18px}.shell{max-width:1440px;margin:0 auto}.trust{height:38px;margin:0 -24px;padding:0 24px;border-bottom:1px solid #58472c;background:#17140e;color:var(--amber);display:flex;align-items:center;justify-content:space-between;font:600 11px/1 var(--mono);letter-spacing:.09em}.trust strong{color:#ffe1a4}.top{height:116px;display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center;border-bottom:1px solid var(--line)}.eyebrow,.kicker{font:600 10px/1.2 var(--mono);letter-spacing:.13em;color:var(--muted);text-transform:uppercase}.top h1{font-size:36px;line-height:1.02;letter-spacing:-.045em;margin:8px 0 7px;max-width:900px}.top p{font-size:14px;line-height:1.45;color:var(--muted);margin:0;max-width:880px}.mark{width:124px;height:62px;border:1px solid var(--line);border-radius:8px;display:grid;place-items:center;background:var(--panel)}.mark b{font-size:22px;letter-spacing:-.04em}.mark small{display:block;color:var(--mint);font:600 9px/1.2 var(--mono);letter-spacing:.11em;text-align:center;margin-top:5px}.timeline{height:74px;display:grid;grid-template-columns:repeat(3,1fr);align-items:center;border-bottom:1px solid var(--line);position:relative}.timeline:before{content:"";height:1px;background:var(--line);position:absolute;left:7%;right:7%;top:36px}.moment{position:relative;display:grid;grid-template-columns:30px 1fr;gap:10px;align-items:center;padding:0 7%;z-index:1}.moment i{width:26px;height:26px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;background:var(--bg);font:600 10px/1 var(--mono);font-style:normal}.moment.verified i{border-color:var(--mint);color:var(--mint)}.moment.corrected i{border-color:var(--coral);color:var(--coral);border-radius:5px}.moment b{display:block;font-size:12px}.moment small{display:block;margin-top:3px;color:var(--muted);font:10px/1.2 var(--mono)}.workspace{display:grid;grid-template-columns:minmax(0,1fr) 336px;gap:12px;padding-top:12px}.main-column{display:grid;grid-template-rows:248px 326px 68px;gap:12px;min-width:0}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden}.panel-head{height:42px;padding:0 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}.panel-head h2{font-size:13px;margin:0;letter-spacing:-.01em}.panel-head code,.panel-head span{font:9px/1 var(--mono);color:var(--muted);letter-spacing:.07em}.graph-wrap{height:205px;padding:10px 14px 12px;display:grid;grid-template-columns:minmax(0,1fr) 208px;gap:14px}.graph{position:relative;border-right:1px solid var(--line);min-width:0}.graph svg{width:100%;height:100%;display:block}.graph .node{fill:var(--raised);stroke:var(--line);stroke-width:1}.graph .root{stroke:var(--mint)}.graph .copy{stroke:#59625e}.graph .correction{stroke:var(--coral)}.graph .edge{stroke:#69736e;stroke-width:1.2;fill:none}.graph .independent{stroke:var(--mint);stroke-width:2}.graph .affected-edge{stroke:var(--coral);stroke-dasharray:4 4}.graph text{fill:var(--text);font-family:var(--sans);font-size:11px}.graph .meta{fill:var(--muted);font-family:var(--mono);font-size:8px;letter-spacing:.06em}.graph-note{display:flex;flex-direction:column;justify-content:center;gap:14px}.proof-line{padding-left:11px;border-left:2px solid var(--line)}.proof-line.mint{border-color:var(--mint)}.proof-line.amber{border-color:var(--amber)}.proof-line b{display:block;font-size:12px;margin-bottom:4px}.proof-line p{margin:0;color:var(--muted);font-size:11px;line-height:1.42}.brief-body{height:283px;display:grid;grid-template-columns:1fr 1fr;column-gap:0}.claim-row{padding:9px 13px;border-bottom:1px solid var(--line);min-width:0}.claim-row:nth-child(odd){border-right:1px solid var(--line)}.claim-row p{font-size:11px;line-height:1.35;margin:5px 0;color:#d9dedb}.claim-row code{display:block;color:var(--dim);font:8.5px/1.2 var(--mono);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.status{display:inline-block;font:600 8px/1 var(--mono);letter-spacing:.07em;text-transform:uppercase;margin-right:8px;color:var(--muted)}.status.verified{color:var(--mint)}.status.attributed,.status.uncertain{color:var(--amber)}.section-label{font-size:10px;color:var(--muted)}.replay{display:grid;grid-template-columns:1fr 34px 1fr;align-items:center;padding:10px 14px}.replay-block b{font-size:11px}.replay-block code{display:block;margin-top:4px;color:var(--muted);font:9px/1.2 var(--mono)}.equals{text-align:center;color:var(--mint);font:700 18px/1 var(--mono)}.replay .right{text-align:right}.impact-rail{min-height:666px}.rail-section{padding:14px;border-bottom:1px solid var(--line)}.rail-section:last-child{border-bottom:0}.rail-title{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.rail-title h2,.rail-title h3{font-size:12px;margin:0}.corrected-label{color:var(--coral);font:700 8px/1 var(--mono);letter-spacing:.09em}.primary-impact{display:grid;grid-template-columns:1fr 1fr;gap:8px}.metric{background:var(--raised);border:1px solid var(--line);border-radius:6px;padding:10px}.metric strong{display:block;font-size:27px;line-height:1;letter-spacing:-.04em}.metric span{display:block;color:var(--muted);font:9px/1.3 var(--mono);text-transform:uppercase;margin-top:6px}.metric.affected{border-color:#633935}.metric.affected strong{color:var(--coral)}.impact-table{width:100%;border-collapse:collapse;margin-top:8px}.impact-table td{padding:7px 0;border-top:1px solid var(--line);font-size:11px}.impact-table td:last-child{text-align:right;font:600 11px/1 var(--mono)}.boundary{border-left:2px solid var(--coral);padding-left:11px}.boundary b{font-size:12px}.boundary p{font-size:11px;line-height:1.45;color:var(--muted);margin:5px 0 0}.integrity{display:flex;align-items:center;gap:9px;color:var(--mint);font-size:11px}.check{width:22px;height:22px;border:1px solid var(--mint);border-radius:50%;display:grid;place-items:center;font:700 11px/1 var(--mono)}.identity{display:grid;grid-template-columns:54px 1fr;gap:8px;align-items:center;margin:7px 0}.identity span{color:var(--dim);font:8px/1 var(--mono);letter-spacing:.08em}.identity code{font:8.5px/1.25 var(--mono);color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.limits{margin:0;padding:0;list-style:none}.limits li{font-size:9.5px;line-height:1.35;color:var(--muted);margin:5px 0;padding-left:11px;position:relative}.limits li:before{content:"—";position:absolute;left:0;color:var(--dim)}.footer{height:28px;display:flex;justify-content:space-between;align-items:end;color:var(--dim);font:8px/1 var(--mono);letter-spacing:.04em}.footer strong{color:var(--muted)}
body{padding-bottom:10px}.trust{height:34px;font-size:10px}.top{height:104px}.top h1{font-size:34px;margin:7px 0 5px}.top p{font-size:13px;line-height:1.4;max-width:920px}.timeline{height:64px}.timeline:before{top:31px}.moment small{font-size:9px}.main-column{grid-template-rows:230px 286px 58px}.panel-head{height:38px}.panel-head h2{font-size:12px}.panel-head code,.panel-head span{font-size:8px}.graph-wrap{height:191px;padding:8px 14px 10px}.graph .independent,.graph .affected-edge{fill:none}.graph-note{gap:12px}.proof-line p{font-size:10px;line-height:1.4}.brief-body{height:247px}.claim-row{padding:7px 13px}.claim-row p{font-size:10.5px;line-height:1.3;margin:4px 0}.claim-row code{font-size:8px}.status{font-size:7.5px}.section-label{font-size:9px}.replay{padding:8px 14px}.replay-block b{font-size:10px}.replay-block code{font-size:8px;margin-top:3px}.impact-rail{min-height:598px}.rail-section{padding:10px 12px}.rail-title{margin-bottom:7px}.rail-title h2,.rail-title h3{font-size:11px}.metric{padding:8px}.metric strong{font-size:24px}.metric span{font-size:8px;margin-top:5px}.impact-table{margin-top:6px}.impact-table td{padding:5px 0;font-size:10px}.impact-table td:last-child{font-size:10px}.boundary{padding-left:10px}.boundary b{font-size:11px}.boundary p{font-size:10px;line-height:1.4;margin-top:4px}.integrity{gap:8px;font-size:10px}.check{width:20px;height:20px;font-size:10px}.identity{margin:5px 0}.identity span{font-size:7.5px}.identity code{font-size:8px}.limits li{font-size:8.5px;line-height:1.3;margin:4px 0}.footer{height:20px;font-size:7.5px}
@media(max-width:900px){body{padding:0 14px 20px}.trust{margin:0 -14px;padding:0 14px}.top{height:auto;padding:22px 0}.top h1{font-size:30px}.mark{display:none}.timeline{height:auto;padding:12px 0;grid-template-columns:1fr}.timeline:before{display:none}.moment{padding:7px 0}.workspace{grid-template-columns:1fr}.main-column{grid-template-rows:auto}.graph-wrap{height:auto;grid-template-columns:1fr}.graph{border-right:0;border-bottom:1px solid var(--line);height:220px}.brief-body{height:auto;grid-template-columns:1fr}.claim-row:nth-child(odd){border-right:0}.impact-rail{min-height:0}.footer{height:auto;padding-top:18px;gap:20px;align-items:start}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}@media print{body{background:#fff;color:#000}.panel,.mark,.metric{background:#fff;border-color:#bbb}.trust{background:#fff;color:#6b4b00}.top p,.proof-line p,.claim-row p,.boundary p,.limits li,.identity code,.graph .meta{color:#444}.graph .node{fill:#fff}.graph text{fill:#000}}
</style>
</head>
<body>
<div class="trust"><span><strong>PREPARED · FROZEN</strong> &nbsp; SYNTHETIC 72-HOUR SCENARIO</span><span>NO LIVE DATA · NO EXTERNAL ACTION</span></div>
<main class="shell">
  <header class="top">
    <div><div class="eyebrow">ACE WORLD INTELLIGENCE / REALITY BRIEF / 0.7.0-RC1</div><h1>One correction reached $impacted_resources downstream resources. The original Brief did not change.</h1><p>Independent corroboration requires a distinct derivation root. ACE computes the correction boundary from admitted lineage—$direct direct, $transitive transitive, $unaffected untouched—without rewriting history.</p></div>
    <div class="mark"><div><b>ACE / WI</b><small>PROVENANCE FIRST</small></div></div>
  </header>
  <section class="timeline" aria-label="Reality timeline">
    <div class="moment"><i>01</i><div><b>Records admitted</b><small>attributed + time-bound</small></div></div>
    <div class="moment verified"><i>02</i><div><b>Independence proven</b><small>2 distinct roots required</small></div></div>
    <div class="moment corrected"><i>03</i><div><b>Correction appended</b><small>impact projected, history retained</small></div></div>
  </section>
  <div class="workspace">
    <div class="main-column">
      <section class="panel" aria-labelledby="graph-title">
        <div class="panel-head"><h2 id="graph-title">Evidence lineage — publishers are not roots</h2><code>$graph_policy</code></div>
        <div class="graph-wrap">
          <div class="graph">
            <svg viewBox="0 0 760 180" role="img" aria-labelledby="svg-title svg-desc">
              <title id="svg-title">Evidence derivation families</title><desc id="svg-desc">Coastal Wire and Harborview derive from the Ledger report and count as one family. The Basin gauge is a second independent family. A correction supersedes the Ledger report.</desc>
              <path class="edge" d="M190 46 H228 C254 46 250 92 276 92"/><path class="edge" d="M190 92 H276"/><path class="independent" d="M502 31 H548 C568 31 568 60 598 60"/><path class="independent" d="M502 105 H548 C568 105 568 82 598 82"/><path class="affected-edge" d="M190 146 C235 146 235 118 276 118"/>
              <rect class="node copy" x="8" y="27" width="182" height="38" rx="6"/><text x="20" y="43">Coastal Wire</text><text class="meta" x="20" y="56">SYNDICATED PUBLISHER</text>
              <rect class="node copy" x="8" y="73" width="182" height="38" rx="6"/><text x="20" y="89">Harborview</text><text class="meta" x="20" y="102">REPRINT PUBLISHER</text>
              <rect class="node correction" x="8" y="127" width="182" height="38" rx="3"/><text x="20" y="143">Ledger correction 114</text><text class="meta" x="20" y="156">SUPERSEDES ↓</text>
              <rect class="node root" x="276" y="78" width="226" height="55" rx="6"/><text x="290" y="98">Ledger report 1088</text><text class="meta" x="290" y="114">DERIVATION ROOT · ONE FAMILY</text>
              <rect class="node root" x="276" y="8" width="226" height="46" rx="6"/><text x="290" y="27">Basin gauge W10</text><text class="meta" x="290" y="41">INDEPENDENT ROOT</text>
              <rect class="node root" x="598" y="45" width="154" height="50" rx="6"/><text x="612" y="65">Corroborated</text><text class="meta" x="612" y="81">2 DISTINCT ROOTS</text>
            </svg>
          </div>
          <div class="graph-note"><div class="proof-line amber"><b>3 publishers ≠ 3 sources</b><p>Coastal Wire and Harborview resolve to the Ledger root. Repetition adds reach, not independence.</p></div><div class="proof-line mint"><b>2 roots = corroborated</b><p>The Ledger report and Basin gauge are admitted as distinct derivation families.</p></div></div>
        </div>
      </section>
      <section class="panel" aria-labelledby="brief-title"><div class="panel-head"><h2 id="brief-title">$brief_title</h2><span>$claim_count CLAIMS · $citation_count CITATIONS · 7 STATUS TYPES</span></div><div class="brief-body">$claim_rows</div></section>
      <section class="panel replay" aria-label="Historical replay proof"><div class="replay-block"><span class="kicker">BEFORE CORRECTION</span><b>Original governed Brief</b><code>$brief_id_short</code></div><div class="equals">=</div><div class="replay-block right"><span class="kicker">AFTER CORRECTION</span><b>Byte-identical replay ✓</b><code>$brief_id_short</code></div></section>
    </div>
    <aside class="panel impact-rail" aria-label="Correction impact boundary">
      <div class="panel-head"><h2>Correction impact</h2><span class="corrected-label">CORRECTED</span></div>
      <section class="rail-section"><div class="primary-impact"><div class="metric affected"><strong>$impacted_resources</strong><span>affected resources</span></div><div class="metric affected"><strong>$impacted_claims</strong><span>affected claims</span></div></div><table class="impact-table"><tr><td>Direct dependencies</td><td>$direct</td></tr><tr><td>Transitive dependencies</td><td>$transitive</td></tr><tr><td>Maximum depth</td><td>$max_depth</td></tr><tr><td>Unaffected boundary</td><td>$unaffected</td></tr></table></section>
      <section class="rail-section"><div class="boundary"><b>Impact means dependency, not falsehood.</b><p>The projection says what used the superseded record. It does not issue a truth verdict. $fully_impacted claims are fully affected; $partially_impacted are partially affected.</p></div></section>
      <section class="rail-section"><div class="integrity"><span class="check">✓</span><div><b>Historical integrity retained</b><br><span class="kicker">NO REWRITE · NO NEW REASONING</span></div></div></section>
      <section class="rail-section"><div class="rail-title"><h3>Proof identities</h3><span class="kicker">AUDITABLE</span></div>$identity_rows</section>
      <section class="rail-section"><div class="rail-title"><h3>Honest limits</h3><span class="kicker">RC1</span></div><ul class="limits">$limit_rows</ul></section>
    </aside>
  </div>
  <footer class="footer"><span><strong>$scenario_id</strong> · AS OF $as_of</span><span>Generated from accepted ACE harnesses · self-contained · deterministic</span></footer>
</main>
<script type="application/json" id="ace-demo-data">$embedded_json</script>
</body></html>
"""
)


def render_html(data: dict[str, Any]) -> str:
    """Render one deterministic, self-contained proof surface."""

    impact = data["correction_impact"]
    embedded = json.dumps(data, sort_keys=True, ensure_ascii=False).replace("</", "<\\/")
    limits = "".join(f"<li>{_e(item)}</li>" for item in data["limits"])
    rendered = _HTML.substitute(
        impacted_resources=impact["impacted_resources"],
        impacted_claims=impact["impacted_claims"],
        direct=impact["direct"],
        transitive=impact["transitive"],
        unaffected=impact["unaffected"],
        max_depth=impact["max_depth"],
        fully_impacted=impact["fully_impacted_claims"],
        partially_impacted=impact["partially_impacted_claims"],
        graph_policy=_e(data["evidence_graph"]["policy"]),
        brief_title=_e(data["brief"]["title"]),
        claim_count=data["brief"]["claim_count"],
        citation_count=data["brief"]["citation_count"],
        claim_rows=_claim_rows(data),
        identity_rows=_identity_rows(data),
        brief_id_short=_e(_short(data["identities"]["brief_id"], 25, 9)),
        limit_rows=limits,
        scenario_id=_e(data["scenario"]["id"]),
        as_of=_e(data["scenario"]["as_of"]),
        embedded_json=embedded,
    )
    return rendered + "\n"


async def write_demo(output_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    data = await collect_demo_data()
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "demo-data.json"
    html_path = output_dir / "index.html"
    data_path.write_text(_canonical_json(data), encoding="utf-8")
    html_path.write_text(render_html(data), encoding="utf-8")
    return data_path, html_path, data


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the frozen ACE World Intelligence public proof surface.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Artifact directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    data_path, html_path, data = asyncio.run(write_demo(args.output_dir.resolve()))
    print(f"World Intelligence public demo: {html_path}")
    print(f"Machine-readable proof: {data_path}")
    print(f"Case: {data['identities']['case_id']}")
    print(f"Brief: {data['identities']['brief_id']}")
    print("Mode: PREPARED / FROZEN (synthetic; not LIVE)")
    return 0


if __name__ == "__main__":  # pragma: no cover - command entry point
    raise SystemExit(main())

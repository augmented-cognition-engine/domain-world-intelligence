"""Build the World AI Command Center page consumed by ACE Atrium.

The artifact is not a second UI and it does not invent presentation-only
intelligence. It runs the accepted recorded-source journey, then queries the
same public, domain-neutral Intelligence resource plane Atrium uses.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ace.application import (
    ActionResourceProjectionReader,
    AgentMemoryResourceProjectionReader,
    AgentResourceProjectionReader,
    CompositeIntelligenceResourceProjectionReader,
    DecisionOutcomeFeedbackResourceProjectionReader,
    IntelligenceLedgerResourceProjectionReader,
    IntelligenceResourcePlaneService,
    LiveSourceResourceProjectionReader,
    MonitoringResourceProjectionReader,
)
from ace.core import GovernedStateHeadPreconditionV1Alpha1
from ace.core.runtime_use import AuthorityUseReceiptV1Alpha1
from ace.intelligence import IntelligenceResourceKind, IntelligenceResourceQueryV1Alpha1

from scripts.ai_command_center_live_acceptance import run_acceptance

READ_GRANT = "authority_grant:world-ai-atrium-read"
READ_KINDS = tuple(IntelligenceResourceKind)


class ExactReadAuthority:
    async def resolve_authority_use(self, **request) -> AuthorityUseReceiptV1Alpha1:
        if (
            request["operation"] != "query_intelligence_resources"
            or request["authority"] != "observe_read"
            or request["grant_ref"] != READ_GRANT
        ):
            raise ValueError("Atrium demo query crossed its exact read boundary")
        context = request["context"]
        return AuthorityUseReceiptV1Alpha1(
            product_id=context.product_id,
            actor_ref=context.actor_ref,
            authenticated_context=context,
            use_subject_ref=request["use_subject_ref"],
            use_subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            authority=request["authority"],
            grant_ref=READ_GRANT,
            grant_hash="9" * 64,
            evaluated_at=request["evaluated_at"],
            expires_at=context.expires_at,
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1(
                state_kind="authority_grant",
                product_id=context.product_id,
                state_id=READ_GRANT,
                sequence=1,
                revision_id="authority_revision:world-ai-atrium-read",
                commit_receipt_id="authority_receipt:world-ai-atrium-read",
            ),
        )


def _reader(store):
    return CompositeIntelligenceResourceProjectionReader(
        ActionResourceProjectionReader(store=store, degrade_unsupported=False),
        AgentMemoryResourceProjectionReader(store=store, degrade_unsupported=False),
        AgentResourceProjectionReader(store=store, degrade_unsupported=False),
        IntelligenceLedgerResourceProjectionReader(store=store, degrade_unsupported=False),
        MonitoringResourceProjectionReader(store=store, degrade_unsupported=False),
        DecisionOutcomeFeedbackResourceProjectionReader(store=store, degrade_unsupported=False),
        LiveSourceResourceProjectionReader(store=store, degrade_unsupported=False),
    )


async def build_atrium_page() -> dict[str, Any]:
    state: dict[str, Any] = {}
    proof = await run_acceptance(state_sink=state)
    environment = state["environment"]
    records = tuple(environment.store.records.values())
    evaluated_at = datetime(2026, 8, 10, 20, 5, tzinfo=UTC)
    request = IntelligenceResourceQueryV1Alpha1(
        authenticated_context=environment.context,
        product_id=environment.context.product_id,
        authority_grant_ref=READ_GRANT,
        resource_kinds=READ_KINDS,
        subject_refs=(),
        as_of=max(record.as_of for record in records),
        available_at=max(record.available_at for record in records),
        page_size=200,
    )
    page = await IntelligenceResourcePlaneService(
        reader=_reader(environment.store),
        authority=ExactReadAuthority(),
    ).query(request, evaluated_at=evaluated_at)
    payload = page.model_dump(mode="json")
    payload["demo"] = {
        "contract": "ace.world-intelligence.atrium-demo/v1alpha1",
        "source_proof_contract": proof["contract"],
        "recorded_transport": True,
        "network_freshness_claimed": False,
        "autonomous_publication": False,
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/atrium-demo/world-ai-resource-page.json"),
    )
    arguments = parser.parse_args()
    payload = asyncio.run(build_atrium_page())
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "product_id": payload["product_id"],
                "resource_count": len(payload["items"]),
                "state": payload["state"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

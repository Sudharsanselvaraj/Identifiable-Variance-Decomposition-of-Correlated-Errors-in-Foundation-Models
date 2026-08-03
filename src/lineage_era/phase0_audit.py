"""HF API audit tooling for re-verifying the Phase 0 record (NOT run).

Phase 0 (2026-08-02) verified ~45 model cards via the HF API
(``/api/models/{id}``): ``createdAt``, ``cardData.base_model``, license, and
established that era = PUBLIC RELEASE DATE (not HF ``createdAt``).

This module provides the audit functions used for periodic re-verification
(see docs/09_Roadmap/Timeline.md: re-run Phase 0 occupancy annually). It is
OFFLINE by default: importing it makes no network calls. Only the explicit
CLI invocation ``python src/lineage_era/phase0_audit.py --verify <repo_id>``
hits the HF API.

Guarding rules (from MASTER_PROMPT.md Phase 0 log):
- meta-llama org is auth-gated; a 401/403 must be reported as UNVERIFIED, not
  as evidence of absence.
- ``createdAt`` is only a sanity bound; the era must come from the public
  release record (4 documented divergences in occupancy.ERA_DIVERGENCES).
"""
from __future__ import annotations

import argparse
import json
import urllib.request

from . import occupancy

HF_API = "https://huggingface.co/api/models/{model_id}"

REQUIRED_FIELDS = ("createdAt", "id", "modelId", "pipeline_tag", "license")


def fetch_model_record(model_id: str, timeout: int = 30) -> dict:
    """Fetch one model card from the HF API. Raises on HTTP error."""
    url = HF_API.format(model_id=model_id)
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_base_model(record: dict) -> object:
    """Return cardData.base_model if present and unambiguous."""
    card = record.get("cardData") or {}
    base = card.get("base_model")
    if isinstance(base, str) and base:
        return base
    if isinstance(base, list) and len(base) >= 1:
        return base
    return None


def verify_era(record: dict, public_release_date: str, quiet: bool = False) -> dict:
    """Check a record against the public release date and flag divergence.

    Returns a dict: {repo_id, createdAt, public_release_date, era_divergence,
    base_model}. ``era_divergence`` is True when the HF ``createdAt`` differs
    from the public release date beyond a reasonable slop (we flag any date
    difference, matching the Phase 0 rule that era is the release date).
    """
    repo_id = record.get("id") or record.get("modelId") or "?"
    created = record.get("createdAt")
    divergence = created is not None and created != public_release_date
    result = {
        "repo_id": repo_id,
        "createdAt": created,
        "public_release_date": public_release_date,
        "era_divergence": bool(divergence),
        "base_model": extract_base_model(record),
    }
    if not quiet:
        print(json.dumps(result, indent=2, default=str))
    return result


def audit_model(repo_id: str, public_release_date: str | None = None) -> dict:
    """Fetch and verify a single model record.

    ``public_release_date`` is optional; when omitted, only createdAt/base_model
    are reported and era divergence is left as "UNKNOWN" (per Phase 0 the era
    must come from the public release record, not the repo timestamp).
    """
    record = fetch_model_record(repo_id)
    base = extract_base_model(record)
    created = record.get("createdAt")
    out = {
        "repo_id": record.get("id") or record.get("modelId"),
        "createdAt": created,
        "base_model": base,
    }
    if public_release_date is not None:
        out.update({
            "public_release_date": public_release_date,
            "era_divergence": created != public_release_date,
        })
    else:
        out["era_divergence"] = "UNKNOWN (supply public_release_date)"
    return out


def _main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="Re-verify a Phase 0 model record via the HF API."
    )
    ap.add_argument("--verify", metavar="REPO_ID",
                    help="Fetch one model record and print a verification summary.")
    ap.add_argument("--release-date", metavar="YYYY-MM-DD", default=None,
                    help="Public release date to compare against HF createdAt.")
    args = ap.parse_args(argv)

    if not args.verify:
        ap.error("no action requested (only --verify is implemented; see README)")

    try:
        summary = audit_model(args.verify, args.release_date)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"UNVERIFIED {args.verify}: {exc!r}")
        return
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    _main()

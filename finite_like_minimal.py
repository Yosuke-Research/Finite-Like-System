"""
Finite-Like System: Minimal Reference Implementation
====================================================
Corresponds to the preprint:
  Finite-Like System: Capacity-Bounded Parallel Maintenance
  and Iterative Reselection
  (Yosuke, April 2026)

This code is structural and illustrative, not domain-calibrated.
All scoring components are domain-dependent evaluation terms;
this implementation specifies their structural role only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


Candidate = Dict[str, Any]
ClassificationResult = Dict[str, List[Candidate]]


# ---------------------------------------------------------------------------
# Scoring Functions (Eqs. 1–3)
# ---------------------------------------------------------------------------

def compute_s_adopt(b_i: Candidate) -> float:
    """
    Eq. (1): S_adopt(b_i) = Δ+ − Δ− + C_ready − H_cost
    Adoption strength / readiness for commitment.
    """
    return (
        b_i["delta_plus"]
        - b_i["delta_minus"]
        + b_i["closure_ready"]
        - b_i["h_cost"]
    )


def compute_s_keep(b_i: Candidate) -> float:
    """
    Eq. (2): S_keep(b_i) = D_value + Δ+ − H_cost
    Retention value / worth as a comparison reference.
    """
    return (
        b_i["d_value"]
        + b_i["delta_plus"]
        - b_i["h_cost"]
    )


def compute_s_reinject(b_i: Candidate) -> float:
    """
    Eq. (3): S_reinject(b_i) = D_value + Δ+ − Δ− − H_cost + F_fresh
    Reinjection score for deferred candidates.
    """
    return (
        b_i["d_value"]
        + b_i["delta_plus"]
        - b_i["delta_minus"]
        - b_i["h_cost"]
        + b_i.get("f_fresh", 0.0)
    )


# ---------------------------------------------------------------------------
# Classification (Section 3)
# ---------------------------------------------------------------------------

def classify_h_set(
    h_set: List[Candidate],
    k_hold: int,
    t_adopt: float,
    t_keep: float,
    max_adopt: int = 2,
) -> ClassificationResult:
    """
    Seven-step classification of H_set into:
      adopt / retain / defer / remove

    max_adopt is a structural heuristic (default 2);
    thresholds are domain-dependent and not calibrated here.
    """
    scored: List[Candidate] = []
    for b_i in h_set:
        c = dict(b_i)
        c["s_adopt"] = compute_s_adopt(c)
        c["s_keep"] = compute_s_keep(c)
        scored.append(c)

    # Step 2: sort by S_adopt descending
    adopt_ranked = sorted(scored, key=lambda x: x["s_adopt"], reverse=True)

    # Step 3: assign adopt (top candidates, up to max_adopt, above threshold)
    adopt: List[Candidate] = []
    remaining: List[Candidate] = []
    for b_i in adopt_ranked:
        if len(adopt) < max_adopt and b_i["s_adopt"] >= t_adopt:
            adopt.append(b_i)
        else:
            remaining.append(b_i)

    # Step 4: sort remaining by S_keep descending
    keep_ranked = sorted(remaining, key=lambda x: x["s_keep"], reverse=True)

    # Step 5: assign retain (up to k_hold)
    retain = keep_ranked[:k_hold]
    leftover = keep_ranked[k_hold:]

    # Steps 6–7: defer if above t_keep, otherwise remove
    defer: List[Candidate] = []
    remove: List[Candidate] = []
    for b_i in leftover:
        if b_i["s_keep"] >= t_keep:
            defer.append(b_i)
        else:
            remove.append(b_i)

    return {
        "adopt": adopt,
        "retain": retain,
        "defer": defer,
        "remove": remove,
    }


# ---------------------------------------------------------------------------
# Reinjection (Section 4)
# ---------------------------------------------------------------------------

def reinject_from_buffer(
    h_next: List[Candidate],
    d_buffer: List[Candidate],
    k_hold: int,
    cooldown_ids: set[str] | None = None,
) -> Tuple[List[Candidate], List[Candidate]]:
    """
    Reinjection from D_buffer into H_next.

    Structural constraints:
      1. No consecutive re-entry (via cooldown_ids)
      2. Type density control (simple priority penalty)
    """
    cooldown_ids = cooldown_ids or set()
    active_types = {b_i["source_type"] for b_i in h_next}

    reinjectable: List[Candidate] = []
    for b_i in d_buffer:
        if b_i["id"] in cooldown_ids:
            continue
        c = dict(b_i)
        penalty = 0.5 if c["source_type"] in active_types else 0.0
        c["s_reinject"] = compute_s_reinject(c) - penalty
        reinjectable.append(c)

    reinject_ranked = sorted(
        reinjectable, key=lambda x: x["s_reinject"], reverse=True
    )

    updated_h_next = list(h_next)
    used_ids: set[str] = set()

    for b_i in reinject_ranked:
        if len(updated_h_next) >= k_hold:
            break
        updated_h_next.append(b_i)
        used_ids.add(b_i["id"])
        active_types.add(b_i["source_type"])

    updated_d_buffer = [b_i for b_i in d_buffer if b_i["id"] not in used_ids]
    return updated_h_next, updated_d_buffer


# ---------------------------------------------------------------------------
# Premise Adaptation (Section 5)
# ---------------------------------------------------------------------------

def compute_outcome_distribution(
    classification: ClassificationResult,
) -> Dict[str, float]:
    """
    Eq. (4): outcome ratios  a_rate, r_rate, d_rate, x_rate.
    """
    total = sum(len(v) for v in classification.values())
    if total == 0:
        return {"a_rate": 0.0, "r_rate": 0.0, "d_rate": 0.0, "x_rate": 0.0}
    return {
        "a_rate": len(classification["adopt"]) / total,
        "r_rate": len(classification["retain"]) / total,
        "d_rate": len(classification["defer"]) / total,
        "x_rate": len(classification["remove"]) / total,
    }


def classify_distribution_pattern(
    rates: Dict[str, float],
    dominance_threshold: float = 0.5,
) -> str:
    """
    Diagnostic pattern classification:
      mixed / adopt-heavy / defer-heavy / remove-heavy
    """
    dominant_key = max(rates, key=rates.get)
    dominant_val = rates[dominant_key]
    if dominant_val < dominance_threshold:
        return "mixed"
    if dominant_key == "a_rate":
        return "adopt-heavy"
    if dominant_key == "d_rate":
        return "defer-heavy"
    if dominant_key == "x_rate":
        return "remove-heavy"
    return "mixed"


def update_premise_structure(
    classification: ClassificationResult,
) -> Dict[str, Any]:
    """
    Premise adaptation pathway:
      outcome distribution → pattern classification → diagnostic

    Does NOT apply domain-specific adjustment rules.
    Returns the structural diagnostic for downstream adaptation.
    """
    rates = compute_outcome_distribution(classification)
    pattern = classify_distribution_pattern(rates)
    return {"outcome_distribution": rates, "distribution_pattern": pattern}


# ---------------------------------------------------------------------------
# Full Cycle
# ---------------------------------------------------------------------------

def run_finite_like_cycle(
    h_set: List[Candidate],
    k_hold: int,
    t_adopt: float,
    t_keep: float,
    cooldown_ids: set[str] | None = None,
) -> Dict[str, Any]:
    """
    Run one minimal Finite‑Like cycle.

    A full cycle consists of classifying the parallel candidate set (H_set)
    into adoption/retention/defer/remove roles (via :func:`classify_h_set`),
    constructing the next active set and deferred buffer, optionally
    reinjecting deferred candidates under structural constraints, and
    updating the premise diagnostic structure.  The returned dictionary
    contains the classification result, the updated active set (H_next),
    the remaining deferred buffer (D_buffer), and the premise diagnostic.
    """
    classification = classify_h_set(h_set, k_hold, t_adopt, t_keep)

    h_next = list(classification["retain"])
    d_buffer = list(classification["defer"])

    h_next, d_buffer = reinject_from_buffer(
        h_next, d_buffer, k_hold, cooldown_ids
    )

    premise = update_premise_structure(classification)

    return {
        "classification": classification,
        "h_next": h_next,
        "d_buffer": d_buffer,
        "premise_diagnostic": premise,
    }


# ---------------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    h_set = [
        {
            "id": "A", "delta_plus": 3.0, "delta_minus": 1.0,
            "closure_ready": 2.0, "h_cost": 1.0, "d_value": 1.0,
            "source_type": "type1", "defer_cycles": 0, "f_fresh": 0.0,
        },
        {
            "id": "B", "delta_plus": 2.4, "delta_minus": 0.8,
            "closure_ready": 1.2, "h_cost": 0.7, "d_value": 1.8,
            "source_type": "type2", "defer_cycles": 1, "f_fresh": 0.2,
        },
        {
            "id": "C", "delta_plus": 1.6, "delta_minus": 0.4,
            "closure_ready": 0.5, "h_cost": 0.5, "d_value": 2.2,
            "source_type": "type3", "defer_cycles": 2, "f_fresh": 0.4,
        },
        {
            "id": "D", "delta_plus": 0.8, "delta_minus": 1.3,
            "closure_ready": 0.2, "h_cost": 0.4, "d_value": 0.6,
            "source_type": "type1", "defer_cycles": 0, "f_fresh": 0.0,
        },
    ]

    result = run_finite_like_cycle(
        h_set=h_set, k_hold=1, t_adopt=2.5, t_keep=1.5,
    )

    print("=== Finite-Like System: 1-cycle example ===\n")

    print("Classification:")
    for role, members in result["classification"].items():
        ids = [b["id"] for b in members]
        scores = []
        for b in members:
            s_a = f'S_adopt={b["s_adopt"]:.2f}'
            s_k = f'S_keep={b["s_keep"]:.2f}'
            scores.append(f'{b["id"]}({s_a}, {s_k})')
        print(f"  {role:8s}: {ids}  {scores}")

    print(f"\nH_next:   {[b['id'] for b in result['h_next']]}")
    print(f"D_buffer: {[b['id'] for b in result['d_buffer']]}")
    print(f"\nPremise diagnostic: {result['premise_diagnostic']}")

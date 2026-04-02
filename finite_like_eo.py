"""
Finite-Like System: EO Monitoring Extension
=============================================
Exploratory Oscillation (EO) monitoring layer for the Finite-Like System.

This file is a stress-test / monitoring extension of the minimal prototype.
It detects exploratory oscillation, evaluates EO termination criteria,
and signals transition to premise adjustment when the oscillation ceases
to be informative.

EO is not a bug — it is a structurally inevitable mode that arises
when premature closure is successfully avoided under finite capacity.
The question is not whether it occurs, but when to exit it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter, deque
from typing import Any, Dict, List, Tuple


Candidate = Dict[str, Any]
ClassificationResult = Dict[str, List[Candidate]]


# ---------------------------------------------------------------------------
# Scoring Functions (Eqs. 1–3)
# ---------------------------------------------------------------------------

def compute_s_adopt(b_i: Candidate) -> float:
    """Eq. (1): S_adopt = Δ+ − Δ− + C_ready − H_cost"""
    return (
        b_i["delta_plus"]
        - b_i["delta_minus"]
        + b_i["closure_ready"]
        - b_i["h_cost"]
    )


def compute_s_keep(b_i: Candidate) -> float:
    """Eq. (2): S_keep = D_value + Δ+ − H_cost"""
    return (
        b_i["d_value"]
        + b_i["delta_plus"]
        - b_i["h_cost"]
    )


def compute_s_reinject(b_i: Candidate) -> float:
    """Eq. (3): S_reinject = D_value + Δ+ − Δ− − H_cost + F_fresh"""
    return (
        b_i["d_value"]
        + b_i["delta_plus"]
        - b_i["delta_minus"]
        - b_i["h_cost"]
        + b_i.get("f_fresh", 0.0)
    )


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_h_set(
    h_set: List[Candidate],
    k_hold: int,
    t_adopt: float,
    t_keep: float,
    max_adopt: int = 2,
) -> ClassificationResult:
    """Seven-step classification into adopt / retain / defer / remove."""
    scored: List[Candidate] = []
    for b_i in h_set:
        c = dict(b_i)
        c["s_adopt"] = compute_s_adopt(c)
        c["s_keep"] = compute_s_keep(c)
        scored.append(c)

    adopt_ranked = sorted(scored, key=lambda x: x["s_adopt"], reverse=True)

    adopt: List[Candidate] = []
    remaining: List[Candidate] = []
    for b_i in adopt_ranked:
        if len(adopt) < max_adopt and b_i["s_adopt"] >= t_adopt:
            adopt.append(b_i)
        else:
            remaining.append(b_i)

    keep_ranked = sorted(remaining, key=lambda x: x["s_keep"], reverse=True)
    retain = keep_ranked[:k_hold]
    leftover = keep_ranked[k_hold:]

    defer: List[Candidate] = []
    remove: List[Candidate] = []
    for b_i in leftover:
        if b_i["s_keep"] >= t_keep:
            defer.append(b_i)
        else:
            remove.append(b_i)

    return {"adopt": adopt, "retain": retain, "defer": defer, "remove": remove}


# ---------------------------------------------------------------------------
# Reinjection (returns reinjected_ids for EO tracking)
# ---------------------------------------------------------------------------

def reinject_from_buffer(
    h_next: List[Candidate],
    d_buffer: List[Candidate],
    k_hold: int,
    cooldown_ids: set[str] | None = None,
) -> Tuple[List[Candidate], List[Candidate], List[str]]:
    """
    Reinjection from D_buffer into H_next.
    Returns: updated_h_next, updated_d_buffer, reinjected_ids
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
    reinjected_ids: List[str] = []

    for b_i in reinject_ranked:
        if len(updated_h_next) >= k_hold:
            break
        updated_h_next.append(b_i)
        used_ids.add(b_i["id"])
        reinjected_ids.append(b_i["id"])
        active_types.add(b_i["source_type"])

    updated_d_buffer = [b_i for b_i in d_buffer if b_i["id"] not in used_ids]
    return updated_h_next, updated_d_buffer, reinjected_ids


# ---------------------------------------------------------------------------
# Premise Adaptation
# ---------------------------------------------------------------------------

def compute_outcome_distribution(
    classification: ClassificationResult,
) -> Dict[str, float]:
    """Eq. (4): outcome ratios."""
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
    """Diagnostic pattern: mixed / adopt-heavy / defer-heavy / remove-heavy"""
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
    """Premise adaptation: distribution → pattern → diagnostic."""
    rates = compute_outcome_distribution(classification)
    pattern = classify_distribution_pattern(rates)
    return {"outcome_distribution": rates, "distribution_pattern": pattern}


# ---------------------------------------------------------------------------
# Exploratory Oscillation Tracker
# ---------------------------------------------------------------------------

@dataclass
class EOTracker:
    """
    Minimal tracker for Exploratory Oscillation (EO).

    EO is a transient operational mode characterized by repeated
    defer <-> reinjection behavior without immediate closure,
    while preserving reselection potential.

    Termination criteria:
      T1: stagnation of distribution pattern
      T2: no score improvement
      T3: reinjection saturation
    """
    window: int = 3
    improvement_epsilon: float = 0.05
    max_reinjections_per_candidate: int = 3

    pattern_history: deque[str] = field(
        default_factory=lambda: deque(maxlen=10)
    )
    mean_keep_history: deque[float] = field(
        default_factory=lambda: deque(maxlen=10)
    )
    mean_adopt_history: deque[float] = field(
        default_factory=lambda: deque(maxlen=10)
    )
    reinjection_counter: Counter = field(default_factory=Counter)

    def update(
        self,
        classification: ClassificationResult,
        reinjected_ids: List[str],
    ) -> None:
        rates = compute_outcome_distribution(classification)
        pattern = classify_distribution_pattern(rates)
        self.pattern_history.append(pattern)

        all_members: List[Candidate] = []
        for role_members in classification.values():
            all_members.extend(role_members)

        if all_members:
            mean_keep = sum(b["s_keep"] for b in all_members) / len(all_members)
            mean_adopt = sum(b["s_adopt"] for b in all_members) / len(all_members)
        else:
            mean_keep = 0.0
            mean_adopt = 0.0

        self.mean_keep_history.append(mean_keep)
        self.mean_adopt_history.append(mean_adopt)

        for cid in reinjected_ids:
            self.reinjection_counter[cid] += 1

    def is_exploratory_oscillation(self) -> bool:
        """Minimal EO detection."""
        if len(self.pattern_history) < self.window:
            return False
        recent = list(self.pattern_history)[-self.window:]
        return any(p in {"mixed", "defer-heavy"} for p in recent)

    def termination_reason(self) -> str | None:
        """
        Returns: 'stagnation' | 'no-improvement' |
                 'reinjection-saturation' | None
        """
        # T1: pattern stagnation
        if len(self.pattern_history) >= self.window:
            recent = list(self.pattern_history)[-self.window:]
            if len(set(recent)) == 1:
                return "stagnation"

        # T2: no improvement
        if (
            len(self.mean_keep_history) >= self.window
            and len(self.mean_adopt_history) >= self.window
        ):
            keep_r = list(self.mean_keep_history)[-self.window:]
            adopt_r = list(self.mean_adopt_history)[-self.window:]
            if (
                max(keep_r) - min(keep_r) < self.improvement_epsilon
                and max(adopt_r) - min(adopt_r) < self.improvement_epsilon
            ):
                return "no-improvement"

        # T3: reinjection saturation
        for _, count in self.reinjection_counter.items():
            if count > self.max_reinjections_per_candidate:
                return "reinjection-saturation"

        return None


# ---------------------------------------------------------------------------
# Full Cycle with EO Monitoring
# ---------------------------------------------------------------------------

def run_finite_like_cycle(
    h_set: List[Candidate],
    k_hold: int,
    t_adopt: float,
    t_keep: float,
    cooldown_ids: set[str] | None = None,
    eo_tracker: EOTracker | None = None,
) -> Dict[str, Any]:
    """
    One Finite-Like cycle with optional EO monitoring:
      classify → H_next / D_buffer → reinject → premise → EO check
    """
    classification = classify_h_set(h_set, k_hold, t_adopt, t_keep)

    h_next = list(classification["retain"])
    d_buffer = list(classification["defer"])

    h_next, d_buffer, reinjected_ids = reinject_from_buffer(
        h_next, d_buffer, k_hold, cooldown_ids
    )

    premise = update_premise_structure(classification)

    eo_state = {
        "is_eo": False,
        "termination_reason": None,
        "transition": None,
    }

    if eo_tracker is not None:
        eo_tracker.update(classification, reinjected_ids)
        is_eo = eo_tracker.is_exploratory_oscillation()
        term = eo_tracker.termination_reason()

        eo_state["is_eo"] = is_eo
        eo_state["termination_reason"] = term
        if term is not None:
            eo_state["transition"] = "premise-adjustment"

    return {
        "classification": classification,
        "h_next": h_next,
        "d_buffer": d_buffer,
        "reinjected_ids": reinjected_ids,
        "premise_diagnostic": premise,
        "eo_state": eo_state,
    }


# ---------------------------------------------------------------------------
# Stress Test: Stagnation-Dominant EO
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    eo_tracker = EOTracker(
        window=3,
        improvement_epsilon=0.05,
        max_reinjections_per_candidate=2,
    )

    h_set = [
        {
            "id": "Z1", "delta_plus": 2.0, "delta_minus": 1.4,
            "closure_ready": 0.5, "h_cost": 0.9, "d_value": 1.8,
            "source_type": "typeZ", "defer_cycles": 2, "f_fresh": 0.6,
        },
        {
            "id": "Z2", "delta_plus": 2.1, "delta_minus": 1.5,
            "closure_ready": 0.4, "h_cost": 0.8, "d_value": 1.7,
            "source_type": "typeZ", "defer_cycles": 2, "f_fresh": 0.5,
        },
        {
            "id": "Z3", "delta_plus": 1.9, "delta_minus": 1.3,
            "closure_ready": 0.6, "h_cost": 0.85, "d_value": 1.6,
            "source_type": "typeZ", "defer_cycles": 3, "f_fresh": 0.7,
        },
    ]

    current_h_set = h_set

    for cycle in range(1, 6):
        print(f"\n=== Cycle {cycle} ===")

        result = run_finite_like_cycle(
            h_set=current_h_set,
            k_hold=1,
            t_adopt=2.5,
            t_keep=1.8,
            cooldown_ids=set(),
            eo_tracker=eo_tracker,
        )

        for role, members in result["classification"].items():
            print(f"{role:>8}: {[b['id'] for b in members]}")

        print("reinjected:", result["reinjected_ids"])
        print("eo_state:", result["eo_state"])
        print("premise:", result["premise_diagnostic"]["distribution_pattern"])

        # Next cycle: retained + deferred
        current_h_set = result["h_next"] + result["d_buffer"]

        # Deferred candidates accumulate freshness
        deferred_ids = {b["id"] for b in result["d_buffer"]}
        for b_i in current_h_set:
            if b_i["id"] in deferred_ids:
                b_i["f_fresh"] = b_i.get("f_fresh", 0.0) + 0.2

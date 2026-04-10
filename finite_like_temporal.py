"""
Finite-Like System: Temporal Deferral
======================================
Reference implementation of margin preservation via temporal
deferral, corresponding to DMM v2.0 §5.4.

This module implements temporal load redistribution (deferral
and reinjection) as a margin preservation mechanism. It is NOT
a rollback mechanism and does not modify the semantics of DMM's
rollback operation.

  - Deferral: when margin falls below threshold, holding elements
    are reassigned to future time indices.
  - Reinjection: deferred elements are reactivated at their
    assigned time, subject to the capacity constraint.

The mechanism operates purely by redistribution. Total load is
conserved; capacity C is unchanged.

Note on `priority`:
The `priority` field in this module has module-local semantics:
higher priority = harder to defer, earlier to reinject.
This differs from `priority` in finite_like_schema.py, where it
contributes to interruption strength. Cross-module unification
of the `priority` semantics is left as future work.

Yosuke (Independent Researcher)
ORCID: 0009-0002-6477-9087
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple


HoldingItem = Dict[str, Any]
DeferredQueue = Dict[int, List[HoldingItem]]


# ---------------------------------------------------------------------------
# Margin Computation
# ---------------------------------------------------------------------------

def compute_margin(
    p: float,
    o: float,
    active_items: List[HoldingItem],
    capacity: float,
) -> float:
    """
    M_t = C - (P_t + O_t + H_t)

    Returns the operational margin at the current time step.
    """
    current_h = sum(item["load"] for item in active_items)
    return capacity - (p + o + current_h)


# ---------------------------------------------------------------------------
# Deferrability Scoring
# ---------------------------------------------------------------------------

def score_deferrability(item: HoldingItem, current_time: int) -> float:
    """
    Score how suitable an item is for deferral.
    Higher score = more deferrable.

    Scoring: (1 - priority) + 0.1 * slack
    Low-priority items with high deadline slack are deferred first.
    Items without deadlines receive zero slack (conservative).
    """
    priority = item.get("priority", 0.5)
    deadline = item.get("deadline")
    if deadline is not None:
        slack = max(deadline - current_time, 0)
    else:
        slack = 0
    return (1.0 - priority) + 0.1 * slack


# ---------------------------------------------------------------------------
# Deferral Step (Appendix A of preprint)
# ---------------------------------------------------------------------------

def deferral_step(
    p: float,
    o: float,
    active_items: List[HoldingItem],
    capacity: float,
    threshold: float,
    current_time: int,
    defer_delta: int = 1,
) -> Tuple[List[HoldingItem], List[Tuple[HoldingItem, int]]]:
    """
    When margin falls below threshold, select holding elements
    for deferral to future time indices.

    Parameters
    ----------
    p : float
        Goal-related load at current time.
    o : float
        Observational load at current time.
    active_items : list of HoldingItem
        Currently active holding elements.
    capacity : float
        Finite capacity bound C.
    threshold : float
        Margin threshold θ below which deferral is triggered.
    current_time : int
        Current discrete time index.
    defer_delta : int
        Default number of time steps to defer (used when item
        has no scheduling preference).

    Returns
    -------
    retained : list of HoldingItem
        Items kept in the active set.
    deferred : list of (HoldingItem, target_time)
        Items removed from active set with their target
        reinjection time.
    """
    margin = compute_margin(p, o, active_items, capacity)

    if margin >= threshold:
        return list(active_items), []

    required_release = threshold - margin

    scored = sorted(
        active_items,
        key=lambda item: score_deferrability(item, current_time),
        reverse=True,
    )

    released = 0.0
    retained: List[HoldingItem] = []
    deferred: List[Tuple[HoldingItem, int]] = []

    for item in scored:
        if released < required_release:
            target_time = current_time + item.get("defer_delta", defer_delta)
            deferred.append((item, target_time))
            released += item["load"]
        else:
            retained.append(item)

    return retained, deferred


# ---------------------------------------------------------------------------
# Reinjection Step (Appendix B of preprint)
# ---------------------------------------------------------------------------

def reinjection_step(
    p: float,
    o: float,
    active_items: List[HoldingItem],
    deferred_queue: DeferredQueue,
    capacity: float,
    current_time: int,
    defer_delta: int = 1,
) -> Tuple[List[HoldingItem], int, DeferredQueue]:
    """
    Reactivate deferred elements at their assigned time index,
    subject to the capacity constraint.

    Elements due at current_time are sorted by priority
    (descending) and reintroduced greedily. Items that cannot
    fit are re-deferred to a later time index.

    Parameters
    ----------
    p : float
        Goal-related load at current time.
    o : float
        Observational load at current time.
    active_items : list of HoldingItem
        Currently active holding elements.
    deferred_queue : DeferredQueue
        Mapping from time index to list of deferred items.
    capacity : float
        Finite capacity bound C.
    current_time : int
        Current discrete time index.
    defer_delta : int
        Default re-deferral offset for items that still
        cannot fit.

    Returns
    -------
    active_items : list of HoldingItem
        Updated active set after reinjection.
    reinjected_count : int
        Number of items successfully reinjected.
    deferred_queue : DeferredQueue
        Updated queue (due items removed or re-deferred).
    """
    due_items = deferred_queue.pop(current_time, [])
    if not due_items:
        return list(active_items), 0, deferred_queue

    due_items_sorted = sorted(
        due_items,
        key=lambda item: item.get("priority", 0.5),
        reverse=True,
    )

    updated_active = list(active_items)
    reinjected = 0

    for item in due_items_sorted:
        current_h = sum(x["load"] for x in updated_active)
        if p + o + current_h + item["load"] <= capacity:
            updated_active.append(item)
            reinjected += 1
        else:
            future_t = current_time + item.get("defer_delta", defer_delta)
            deferred_queue.setdefault(future_t, []).append(item)

    return updated_active, reinjected, deferred_queue


# ---------------------------------------------------------------------------
# Full Time Step (deferral + reinjection combined)
# ---------------------------------------------------------------------------

def run_temporal_step(
    p: float,
    o: float,
    active_items: List[HoldingItem],
    deferred_queue: DeferredQueue,
    capacity: float,
    threshold: float,
    current_time: int,
    defer_delta: int = 1,
) -> Dict[str, Any]:
    """
    Execute one temporal deferral cycle:
      1. Reinjection of items due at current_time.
      2. Deferral if margin falls below threshold.

    Reinjection precedes deferral: items returning from the
    deferred queue may themselves be re-deferred if the margin
    is insufficient after reinjection.

    Returns a diagnostic dict with margin, counts, and queues.
    """
    # Phase 1: reinjection
    active, reinjected, deferred_queue = reinjection_step(
        p, o, active_items, deferred_queue, capacity, current_time,
        defer_delta,
    )

    # Phase 2: deferral
    retained, newly_deferred = deferral_step(
        p, o, active, capacity, threshold, current_time, defer_delta,
    )

    # Merge newly deferred items into queue
    for item, target_time in newly_deferred:
        deferred_queue.setdefault(target_time, []).append(item)

    margin_after = compute_margin(p, o, retained, capacity)

    return {
        "active_items": retained,
        "deferred_queue": deferred_queue,
        "margin": margin_after,
        "reinjected_count": reinjected,
        "deferred_count": len(newly_deferred),
        "active_count": len(retained),
        "queue_size": sum(len(v) for v in deferred_queue.values()),
    }


# ---------------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    capacity = 10.0
    threshold = 2.0

    items: List[HoldingItem] = [
        {"id": "h1", "load": 2.5, "priority": 0.9},
        {"id": "h2", "load": 2.0, "priority": 0.5},
        {"id": "h3", "load": 1.5, "priority": 0.3},
        {"id": "h4", "load": 1.0, "priority": 0.2},
    ]

    deferred_queue: DeferredQueue = {}

    print("=== Finite-Like System: Temporal Deferral ===\n")
    print(f"Capacity C = {capacity},  Threshold θ = {threshold}\n")

    # Simulate 6 time steps with varying P and O
    load_schedule = [
        (2.0, 1.5),   # t=0: moderate
        (3.0, 2.0),   # t=1: increasing
        (4.0, 2.5),   # t=2: high pressure
        (2.0, 1.0),   # t=3: relief
        (1.5, 1.0),   # t=4: low
        (1.0, 0.5),   # t=5: minimal
    ]

    active = list(items)

    for t, (p, o) in enumerate(load_schedule):
        result = run_temporal_step(
            p=p, o=o,
            active_items=active,
            deferred_queue=deferred_queue,
            capacity=capacity,
            threshold=threshold,
            current_time=t,
        )

        active = result["active_items"]
        deferred_queue = result["deferred_queue"]

        active_ids = [x["id"] for x in active]
        queue_contents = {
            k: [x["id"] for x in v]
            for k, v in sorted(deferred_queue.items())
        }

        print(f"t={t}  P={p}  O={o}")
        print(f"  margin={result['margin']:.1f}  "
              f"active={active_ids}  "
              f"reinjected={result['reinjected_count']}  "
              f"deferred={result['deferred_count']}")
        if queue_contents:
            print(f"  queue={queue_contents}")
        print()

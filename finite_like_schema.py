"""
Minimal reference implementation of the Finite-Like System with Schema
Compression and Dynamic Unfreezing.

This module defines a `Schema` class that represents a compressed sequence of
actions (candidates).  It provides helper functions to compute interruption
and continuation scores and a predicate to determine whether a schema should
be broken when a new candidate arrives.  The implementation is intentionally
simple and omits domain-specific scoring (e.g. concrete definitions of
`delta_plus` and `delta_minus`).

Example:

    from finite_like_schema import Schema, should_break_schema, run_with_schema

    # Define two candidate actions with simple cost structures
    b1 = {"id": "take", "h_cost": 1.0, "delta_plus": 0.2, "delta_minus": 0.1, "priority": 0.0}
    b2 = {"id": "use",  "h_cost": 1.0, "delta_plus": 0.3, "delta_minus": 0.1, "priority": 0.0}
    b3 = {"id": "return", "h_cost": 1.0, "delta_plus": 0.1, "delta_minus": 0.1, "priority": 0.0}

    schema = Schema([b1, b2, b3], chunk_bonus=1.5, break_cost=1.0, min_break_margin=0.5)

    # Simulate interruption
    interrupting = {"id": "hazard", "delta_plus": 0.9, "delta_minus": 0.0, "priority": 0.5}
    action = run_with_schema(schema, interrupting, delta_avail=1.0)
    print(action)  # 'SCHEMA_BREAK' if unfreezing conditions are met

"""

from __future__ import annotations
from typing import Dict, List, Any


Candidate = Dict[str, Any]


class Schema:
    """A compressed sequence of candidates with associated parameters.

    Args:
        sequence: Ordered list of candidate dictionaries.  Each candidate must
            contain at least the key ``"h_cost"`` representing maintenance cost.
        chunk_bonus: Positive value representing the cost reduction gained by
            compressing the sequence into a single schema.
        break_cost: Positive value representing the cost to interrupt (break)
            the schema and return to explicit evaluation.
        min_break_margin: Minimum operational margin required to safely break
            the schema.  If the available margin is less than this value,
            unfreezing will not occur even if interruption is otherwise
            desirable.
    """

    def __init__(
        self,
        sequence: List[Candidate],
        *,
        chunk_bonus: float = 1.0,
        break_cost: float = 1.0,
        min_break_margin: float = 1.0,
    ) -> None:
        if not sequence:
            raise ValueError("Schema sequence must not be empty")
        if chunk_bonus < 0 or break_cost < 0 or min_break_margin < 0:
            raise ValueError("Schema parameters must be non-negative")
        self.sequence: List[Candidate] = sequence
        self.chunk_bonus = chunk_bonus
        self.break_cost = break_cost
        self.min_break_margin = min_break_margin
        self.active: bool = True

    def schema_cost(self) -> float:
        """Return the maintenance cost of the compressed schema.

        Computed as the sum of the constituent candidate costs minus the
        chunking bonus.
        """
        return sum(b.get("h_cost", 0.0) for b in self.sequence) - self.chunk_bonus


def compute_interrupt_score(b: Candidate) -> float:
    """Compute the interruption score for a candidate.

    Combines positive and negative contributions along with an optional
    priority term.  If keys are missing, defaults are zero.
    """
    return (
        b.get("delta_plus", 0.0)
        - b.get("delta_minus", 0.0)
        + b.get("priority", 0.0)
    )


def compute_continue_score(schema: Schema) -> float:
    """Eq. (5.2) continuation score for a schema.

    Computes the residual value of continuing execution under the current
    schema.  In the theoretical formulation, the continuation value is
    defined as the sum of the stability reward minus the remaining
    maintenance cost of the schema:

        S_continue = R_stability - H_cost_schema

    The schema's maintenance cost already accounts for the chunk bonus
    (i.e. ``schema_cost()`` internally subtracts the ``chunk_bonus``), so
    the chunk bonus should **not** be added again here.  A schema may
    optionally carry a ``stability`` attribute representing an additional
    reward for persisting with the compressed sequence.  If absent,
    ``stability`` defaults to zero.
    """
    stability = getattr(schema, "stability", 0.0)
    # Do not add the chunk bonus again: schema_cost() already includes the
    # reduction from compression (see Schema.schema_cost).  Only the
    # stability reward remains against the maintenance cost.
    return stability - schema.schema_cost()


def should_break_schema(
    schema: Schema, b_new: Candidate, delta_avail: float
) -> bool:
    """Determine whether an active schema should be broken.

    Returns ``True`` when the interruption value exceeds the continuation
    value by at least the schema's break cost, and there is sufficient
    operational margin to perform the break.
    """
    s_interrupt = compute_interrupt_score(b_new)
    s_continue = compute_continue_score(schema)
    value_condition = (s_interrupt - s_continue - schema.break_cost) > 0.0
    margin_condition = delta_avail >= schema.min_break_margin
    return value_condition and margin_condition


def run_with_schema(
    schema: Schema, incoming_candidate: Candidate, delta_avail: float
) -> str:
    """Simulate one cycle of schema execution with a potential interruption.

    If the schema is active and the unfreezing conditions are met, the schema
    will be marked inactive and 'SCHEMA_BREAK' is returned.  Otherwise,
    'FAST_TRACK' is returned if the schema continues to execute; if the
    schema is already inactive, 'NORMAL_FLOW' is returned.
    """
    if schema.active:
        if should_break_schema(schema, incoming_candidate, delta_avail):
            schema.active = False
            return "SCHEMA_BREAK"
        # Otherwise the schema continues via fast-track
        return "FAST_TRACK"
    return "NORMAL_FLOW"
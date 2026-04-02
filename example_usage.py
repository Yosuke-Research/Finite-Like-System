"""
Example script demonstrating schema compression and dynamic unfreezing.

This script constructs a simple schema representing the routine
``take → use → return`` and then injects an interrupting candidate to
illustrate how the unfreezing logic decides whether to break the schema.

Run this file with Python to observe the printed state transitions.
"""

from finite_like_schema import Schema, run_with_schema


def main() -> None:
    # Define three dummy candidates with maintenance costs and basic scoring
    b1 = {
        "id": "take",
        "h_cost": 1.0,
        "delta_plus": 0.2,
        "delta_minus": 0.1,
        "priority": 0.0,
    }
    b2 = {
        "id": "use",
        "h_cost": 1.0,
        "delta_plus": 0.3,
        "delta_minus": 0.1,
        "priority": 0.0,
    }
    b3 = {
        "id": "return",
        "h_cost": 1.0,
        "delta_plus": 0.1,
        "delta_minus": 0.1,
        "priority": 0.0,
    }

    # Create a schema with a chunk bonus and break cost
    schema = Schema([b1, b2, b3], chunk_bonus=1.5, break_cost=1.0, min_break_margin=0.5)
    print("Schema created and active:", schema.active)

    # Simulate a cycle with no interruption
    no_interruption = {"id": "idle", "delta_plus": 0.0, "delta_minus": 0.0, "priority": 0.0}
    result = run_with_schema(schema, no_interruption, delta_avail=1.0)
    print("Cycle 1, result:", result, "| Schema active:", schema.active)

    # Inject a high-priority interrupting candidate
    interrupting = {"id": "hazard", "delta_plus": 0.9, "delta_minus": 0.0, "priority": 0.5}
    result = run_with_schema(schema, interrupting, delta_avail=1.0)
    print("Cycle 2, result:", result, "| Schema active:", schema.active)

    # Another cycle after the schema has been broken
    result = run_with_schema(schema, interrupting, delta_avail=1.0)
    print("Cycle 3, result:", result, "| Schema active:", schema.active)

    # --- Proposition 1: Rigid Persistence under Margin Loss ---
    print("\n--- Proposition 1: Margin Loss Demo ---")
    schema2 = Schema([b1, b2, b3], chunk_bonus=1.5, break_cost=1.0, min_break_margin=0.5)

    # Same high-priority hazard, but margin is now too low to safely break
    result = run_with_schema(schema2, interrupting, delta_avail=0.3)
    print("Low margin, result:", result, "| Schema active:", schema2.active)
    print("  -> Schema persists despite recognizing the need for change")


if __name__ == "__main__":
    main()
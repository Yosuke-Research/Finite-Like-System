# Finite-Like System — Technical Details

## Paper–Code Correspondence

### Finite-Like System

| Paper | Function | Description |
|---|---|---|
| Eq. (1): S_adopt | `compute_s_adopt()` | Adoption strength |
| Eq. (2): S_keep | `compute_s_keep()` | Retention value |
| Eq. (3): S_reinject | `compute_s_reinject()` | Reinjection score |
| §3.2: 7-step classification | `classify_h_set()` | 4-role classification |
| §4: Reinjection | `reinject_from_buffer()` | Conditional reinjection |
| §5: Premise adaptation | `update_premise_structure()` | Premise update |

### Schema Compression

| Paper | Function / Class | Description |
|---|---|---|
| §3: Schema definition | `Schema` class | Compressed action sequence |
| §5.1: S_interrupt | `compute_interrupt_score()` | Interruption value |
| §5.2: S_continue | `compute_continue_score()` | Schema continuation value |
| §5.3–5.4: Unfreezing | `should_break_schema()` | Value condition + margin condition |
| Proposition 1 | margin demo in `example_usage.py` | Rigid persistence under margin loss |

## Core Concepts

| Concept | Symbol | Role |
|---|---|---|
| Parallel Candidate Set | H_set | Candidates maintained in parallel |
| Hold Capacity | K_hold | Upper bound on simultaneous candidates |
| Adoption Strength | S_adopt | Whether to execute now |
| Retention Value | S_keep | Value of keeping for comparison |
| Schema | M | Compressed action sequence |
| Chunk Bonus | B_chunk | Cost reduction from compression |
| Break Cost | C_break | Cost of dissolving a schema |
| Operational Margin | Δ_avail | Available margin for safe unfreezing |

## Exploratory Oscillation (EO) Monitoring

The mechanism that prevents premature closure can itself produce stagnation — a state in which candidates cycle between defer and reinjection without convergence. `finite_like_eo.py` detects the following termination conditions:

1. **Stagnation:** Distribution pattern stops changing
2. **No-Improvement:** No score improvement observed
3. **Reinjection-Saturation:** Same candidates repeatedly cycle through defer and reinjection

On detection, the system issues `transition: 'premise-adjustment'`, prompting reconstruction of the premise structure.

### EO Modes (Observed)

1. **Stagnation EO** — distribution unchanged
2. **Reinjection-loop EO** — same candidates repeatedly reinjected
3. **Non-improving chaotic EO** — distribution fluctuates without improvement

> closure is continuously avoided without yielding informative transition

See `example_output.md` for annotated output.

## Extended Quick Start

### Core (candidate classification and reselection)

```bash
python3 finite_like_minimal.py
```

Four candidates are classified into Adopt / Retain / Defer / Remove.

### Schema (compression and dynamic unfreezing)

```bash
python3 example_usage.py
```

Expected output:

```
Schema created and active: True
Cycle 1, result: FAST_TRACK | Schema active: True
Cycle 2, result: SCHEMA_BREAK | Schema active: False
Cycle 3, result: NORMAL_FLOW | Schema active: False

--- Proposition 1: Margin Loss Demo ---
Low margin, result: FAST_TRACK | Schema active: True
  -> Schema persists despite recognizing the need for change
```

- Cycle 1: Schema executes via fast-track (compression active)
- Cycle 2: High-priority interruption triggers schema dissolution
- Proposition 1: When margin is insufficient, the schema persists even if interruption is recognized — structural reproduction of being unable to change despite awareness

## Future Work

The present architecture assumes a single bounded system. In practical settings, capacity limitations may necessitate delegation, distributed coordination, or external reference mechanisms. These extensions suggest a transition from individual to network-level finite-capacity systems, which is left for future work.

## Citation

```bibtex
@misc{yosuke2026finitelike,
  author = {Yosuke},
  title  = {Finite-Like System: Capacity-Bounded Parallel Maintenance
            and Iterative Reselection},
  year   = {2026},
  note   = {Preprint}
}

@misc{yosuke2026schema,
  author = {Yosuke},
  title  = {Schema Compression and Dynamic Unfreezing
            under Finite Capacity},
  year   = {2026},
  note   = {Preprint}
}
```

# Example Output: EO Monitoring Stress Test

This example shows a **stagnation-dominant EO (Exploratory Oscillation)** pattern.

Under stress-test parameters (`k_hold=1`, `t_adopt=2.5`, `t_keep=1.8`),
the system repeatedly classifies the same candidates into a defer-heavy structure.
The EO monitoring layer detects that the outcome pattern is no longer informative
and requests transition to `premise-adjustment`.

## Console Output

```text
=== Cycle 1 ===
   adopt: []
  retain: ['Z2']
   defer: ['Z1', 'Z3']
  remove: []
reinjected: []
eo_state: {'is_eo': False, 'termination_reason': None, 'transition': None}
premise: defer-heavy

=== Cycle 2 ===
   adopt: []
  retain: ['Z2']
   defer: ['Z1', 'Z3']
  remove: []
reinjected: []
eo_state: {'is_eo': False, 'termination_reason': None, 'transition': None}
premise: defer-heavy

=== Cycle 3 ===
   adopt: []
  retain: ['Z2']
   defer: ['Z1', 'Z3']
  remove: []
reinjected: []
eo_state: {'is_eo': True, 'termination_reason': 'stagnation', 'transition': 'premise-adjustment'}
premise: defer-heavy
```

## Interpretation

### Cycle 1–2

No candidate reaches the adoption threshold.
Z2 is retained; Z1 and Z3 are deferred.
The pattern is already defer-heavy, but EO is not yet confirmed
(the observation window requires 3 cycles).

### Cycle 3

The EO monitoring layer detects that the same defer-heavy pattern
has persisted for the configured observation window (3 cycles).

- `is_eo = True` — the system recognises it is in exploratory oscillation
- `termination_reason = "stagnation"` — the pattern is no longer changing
- `transition = "premise-adjustment"` — the system requests premise update

## Structural Meaning

This output demonstrates that:

1. **Defer-heavy cycling is detected as an EO state** — not a crash
2. **When EO ceases to be informative, the system signals premise adjustment**
3. **The system does not loop forever** — it self-diagnoses and requests mode transition

In this sense, EO functions as a **monitored exploration mode**
rather than an uncontrolled infinite loop.
Avoiding premature closure does not mean tolerating infinite deferral.

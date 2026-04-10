# Finite-Like System

⚠️ **Status: Prototype / Reference Implementation**

**Capacity-Bounded Parallel Maintenance, Iterative Reselection, and Schema Compression**

This repository is a structural reference implementation of the Finite-Like System under finite capacity.  
It is not production code.

## What this repository contains

This repository provides a minimal executable reference for:

- bounded parallel candidate maintenance
- iterative reselection under finite capacity
- schema compression and dynamic unfreezing
- exploratory oscillation (EO) monitoring
- temporal deferral (margin preservation)

The code is intended as an implementation-level companion to the corresponding preprints, not as a domain-calibrated application.

## Files

- `finite_like_minimal.py` — core minimal architecture (classification, reinjection, premise update)
- `finite_like_schema.py` — schema compression and dynamic unfreezing
- `finite_like_eo.py` — EO monitoring extension
- `finite_like_temporal.py` — temporal deferral (margin preservation, DMM v2.0 §5)
- `example_usage.py` — minimal schema demo

## Quick Start

Run the core minimal example:

```bash
python3 finite_like_minimal.py
```

Run the schema demo:

```bash
python3 example_usage.py
```

Run EO monitoring:

```bash
python3 finite_like_eo.py
```

Run temporal deferral:

```bash
python3 finite_like_temporal.py
```
See also: [`example_output.md`](./example_output.md)

For technical notes and paper–code correspondence, see [`DETAILS.md`](./DETAILS.md).

## Author

**Yosuke**  
Independent Researcher  
ORCID: https://orcid.org/0009-0002-6477-9087

## Papers

### Core Papers

- **Finite-Like System**  
  Zenodo: https://zenodo.org/records/19381848  
  DOI: https://doi.org/10.5281/zenodo.19381848

- **Schema Compression and Dynamic Unfreezing**  
  Zenodo: https://zenodo.org/records/19382268  
  DOI: https://doi.org/10.5281/zenodo.19382268

- **Global OASC Framework**  
  Zenodo: https://zenodo.org/records/18264328  
  DOI: https://doi.org/10.5281/zenodo.18264328

- **Drift Management Module (DMM) v2.0**  
  Zenodo: https://zenodo.org/records/19228227  
  DOI: https://doi.org/10.5281/zenodo.19228227

<details>
<summary><strong>Finite Capacity Series (related papers)</strong></summary>

<br>

- **Capacity-Bounded Dynamical Model of Working Memory**  
  Zenodo: https://zenodo.org/records/18843808  
  DOI: https://doi.org/10.5281/zenodo.18843808

- **Situation Representation under Finite Capacity (TST)**  
  Zenodo: https://zenodo.org/records/18974352  
  DOI: https://doi.org/10.5281/zenodo.18974352

- **Structural Divergence in Communication**  
  Zenodo: https://zenodo.org/records/19158630  
  DOI: https://doi.org/10.5281/zenodo.19158630

- **Historical Deformation of Situation–Affine Mapping**  
  Zenodo: https://zenodo.org/records/19228959  
  DOI: https://doi.org/10.5281/zenodo.19228959

- **Operational Safety Conditions under Finite Capacity (ΔASC)**  
  Zenodo: https://zenodo.org/records/19229000  
  DOI: https://doi.org/10.5281/zenodo.19229000

- **Series Note: Two-Layer Structure of Finite Capacity Systems**  
  Zenodo: https://zenodo.org/records/19229297  
  DOI: https://doi.org/10.5281/zenodo.19229297

</details>

## Notes

- This repository is a **reference implementation**, not production software.
- Scoring functions are structural placeholders and remain domain-dependent.
- The implementation preserves structural consistency with the associated preprints.
- `finite_like_temporal.py` implements temporal deferral as a reference implementation of margin preservation in DMM v2.0 §5. It is not a rollback mechanism and does not modify the semantics of DMM's rollback operation.

## License

MIT

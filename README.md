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

The code is intended as an implementation-level companion to the corresponding preprints, not as a domain-calibrated application.

## Files

- `finite_like_minimal.py` — core minimal architecture (classification, reinjection, premise update)
- `finite_like_schema.py` — schema compression and dynamic unfreezing
- `finite_like_eo.py` — EO monitoring extension
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
See also: [`example_output.md`](./example_output.md)

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

<details>
<summary><strong>Finite Capacity Series</strong></summary>

<br>

- **OASC**  
  Zenodo: https://zenodo.org/records/18264328  
  DOI: https://doi.org/10.5281/zenodo.18264328

- **CBDM**  
  Zenodo: https://zenodo.org/records/18843808  
  DOI: https://doi.org/10.5281/zenodo.18843808

- **TST**  
  Zenodo: https://zenodo.org/records/18974352  
  DOI: https://doi.org/10.5281/zenodo.18974352

- **SD**  
  Zenodo: https://zenodo.org/records/19158630  
  DOI: https://doi.org/10.5281/zenodo.19158630

- **HD**  
  Zenodo: https://zenodo.org/records/19228959  
  DOI: https://doi.org/10.5281/zenodo.19228959

- **D-ASC**  
  Zenodo: https://zenodo.org/records/19229000  
  DOI: https://doi.org/10.5281/zenodo.19229000

- **Series Note**  
  Zenodo: https://zenodo.org/records/19229297  
  DOI: https://doi.org/10.5281/zenodo.19229297

- **DMM v2.0**  
  Zenodo: https://zenodo.org/records/19228227  
  DOI: https://doi.org/10.5281/zenodo.19228227

</details>

## Notes

- This repository is a **reference implementation**, not production software.
- Scoring functions are structural placeholders and remain domain-dependent.
- The implementation is intended to preserve consistency with the associated preprints.

## License

MIT

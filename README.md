# Withdrawal Authorization: Research Evaluation Artifact

This repository contains a **local Python reference model** for exact transaction-intent binding, signed attestation checks, replay and expiry rejection, and atomic budget reservations. The included experiments use **synthetic cases**; this is **not** production cryptocurrency signing software, MPC, hardware attestation, an exchange deployment, or a live-blockchain experiment.

The repository's final scholarly title, authors, and associated manuscript citation must be supplied by the authors before archival publication.

## Repository contents

- `src/evaluate.py`: local evaluation, test cases, simulation, and CSV/JSON generation.
- `src/figures_short.py`: figures and LaTeX timing macro generation from `results/summary.json`.
- `results/attack_trials.csv`: 1,200 synthetic attack-case records (12 constructed scenarios × 100 seeds).
- `results/summary.json`: reported counts, local timing, model exploration, and environment metadata.
- `results/macros.tex`: LaTeX timing macro values in the submitted package; see consistency note below.
- `figures/architecture.pdf` and `.png`: architecture illustration.
- `figures/loss_bound.pdf` and `.png`: chart of synthetic admitted values versus epoch budgets.

## Requirements

The included recorded run reports Python **3.11.5** on Windows. Use Python 3.11 where possible. Install the dependencies listed in `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

These requirements specify package names only because the supplied artifact does not identify the exact installed versions of `cryptography` and `matplotlib`. Before claiming an exact environment recreation, record the dependency versions used for the archived experiments.

## Reproduce the experiments

From the repository root:

```powershell
python src/evaluate.py
python src/figures_short.py
```

The first command writes `results/attack_trials.csv` and `results/summary.json`. The second command regenerates the figure files and `results/macros.tex` from the current summary. Both commands **overwrite** some included outputs. Make a copy of the archived results first if you need to compare the original run with regenerated results. Execution times and platform metadata can change between runs.

The code only uses local generated test cases and locally generated Ed25519 key pairs; it does not connect to a cryptocurrency exchange or broadcast transactions. It should nevertheless be reviewed before use or modification in any other environment.

## Scope of the recorded results

- 12 constructed attack categories with 100 seeds each; the included CSV records 1,200 rejected cases under the proposed gate.
- 3,000 valid local evaluations in the benign timing workload.
- 20 repetitions of a SQLite concurrency scenario.
- Additional constructed ablation, outage, residual-budget and bounded-state exploration results.

These results do not establish production-system exploit prevention, network service latency, operational fault tolerance, or hardware security properties.

## CHECK BEFORE PUBLISHING: mismatch in supplied timing outputs

The supplied `results/summary.json` records `benign.p50_ms = 0.73905`, whereas the supplied `results/macros.tex` contains `\LocalMedian = 0.234`. Both files have been **preserved byte-for-byte** from the uploaded ZIP. The mismatch may reflect runs at different times; this cause has **not** been verified.

Before releasing an archival version, check which output corresponds to the manuscript and regenerate or reconcile the macros with the appropriate confirmed run. Do not change the manuscript's numerical claims without documenting the new measured run and its environment.

## Publishing and citation

To publish an archive for citation:

1. Verify results, check for confidential content, and select a software license for which you have the rights.
2. Publish this folder as a public GitHub repository, preserving the folders rather than uploading a single ZIP as the entire repository.
3. Link that repository to Zenodo and enable GitHub archival.
4. Create a GitHub release (for example `v1.0.0`) and obtain the **version-specific Zenodo DOI**.
5. Cite the published Zenodo software record in the manuscript's Data Availability Statement and bibliography.

Alternatively, upload the finalized archive directly to Zenodo as a **Software** record to obtain a DOI without GitHub.

**No license is supplied in this prepared archive.** Choose and add one if you intend to grant code-reuse rights; do not assert a license you do not have authority to grant.

<div align="center">

<img src="assets/banner.png" alt="001 — No Magic | File Fragment Classification" width="100%" />

![Status](https://img.shields.io/badge/status-active-17A398?style=flat-square)
![Type](https://img.shields.io/badge/type-ML%20experiment-17A398?style=flat-square)
![Experiment](https://img.shields.io/badge/experiment-001-17A398?style=flat-square)

**No Magic — File Fragment Classification**

[← Edgewake Experiments](../README.md)

</div>

---

## Overview

Can a machine-learning model identify a file's format from an arbitrary fragment of its contents, without relying on the filename, extension or identifying header?

Known as **file fragment classification**, this is an established problem in digital forensics.

**No Magic** is a practical introduction to machine learning, comparing simple statistical methods, classical ML and small neural networks using ordinary computing hardware.

The aim is to understand dataset preparation, model training and evaluation rather than develop a novel forensic tool.

## Why No Magic?

Many file formats contain recognisable sequences of bytes known as **magic numbers** or **file signatures**. These allow tools such as the Unix `file` command to identify a file's format without relying on its extension.

For example, JPEG files commonly begin with `FF D8 FF`, while ZIP archives often begin with `50 4B 03 04`.

But what happens when we only have a fragment from somewhere in the middle of a file, with no identifying header?

That's the idea behind **No Magic**. We deliberately remove the easy answer and investigate whether the remaining bytes tell us enough to identify the format.

No magic numbers. No assumptions. Just data, measurements and a little machine learning.

For more information, see the [list of file signatures](https://en.wikipedia.org/wiki/List_of_file_signatures) or the [magic(5) documentation](https://man.openbsd.org/magic.5) describing the patterns used by the `file` utility.

## What We'll Explore

- Creating labelled datasets from known file formats.
- Extracting binary fragments without identifying signatures.
- Comparing statistical baselines, classical ML and small neural networks.
- Evaluating performance on previously unseen files.
- Measuring accuracy, training time and inference cost.
- Understanding where different approaches succeed or fail.

## Initial Approach

We'll begin with a small selection of common file formats and fixed-size binary fragments.

| Approach | Purpose |
|---|---|
| **Statistical baseline** | Establish what simple byte statistics can reveal |
| **Random Forest** | Explore classical machine learning |
| **Small neural network** | Compare learned features against simpler methods |

Training and test data will be separated by source file to reduce leakage, with attention to duplicate content and common file generators.

Initial experiments will run on a development laptop without requiring GPU acceleration.

## Progress

The initial work has focused on building a reproducible data-preparation pipeline, understanding the characteristics of individual file fragments and establishing a defensible experimental methodology.

Completed so far:

- Verified source acquisition with pinned SHA-256 checksums.
- Reproducible BMP and ZIP sample generation.
- Deterministic fragment extraction.
- Statistical analysis and visualisation.
- **Result 001:** Initial fragment statistics and observations.

Currently investigating:

- **Result 002:** Dataset design, source independence, sampling strategy and dataset-size justification.

No models have been trained yet. The current work establishes the data and evaluation foundations needed to investigate them reliably.

## Results

Each investigation records its methodology, observations, supporting data and limitations.

### 001 — File Fragment Statistics

**Can simple byte-level statistics distinguish fragments from different file formats?**

An initial investigation of 63 fragments across TXT, JPEG, BMP and ZIP, examining Shannon entropy, printable-byte fraction and zero-byte fraction.

The results show clear differences in some cases, substantial variation within others, and interesting similarities between compressed formats.

**[Read Result 001 — File Fragment Statistics](results/001-fragment-statistics/README.md)**

[View plots](results/001-fragment-statistics/figures/001-fragment-statistics.png) · [Raw measurements](results/001-fragment-statistics/data/001-fragment-statistics.csv)

### 002 — Dataset Design and Construction

**How can we construct a reproducible dataset that supports credible file-fragment classification across independent files?**

Building on the observations from Result 001, this investigation examines how we select, sample and organise the data used in subsequent machine-learning experiments.

The investigation considers the justification for our four file formats and 4 KiB fragments, source-file independence, dataset diversity and the statistical reasoning behind dataset size.

The objective is not simply to collect more data, but to establish a defensible and reproducible foundation for training and evaluating classifiers.

**Status: In progress** — Initial scope, hypotheses and methodological rationale established. Dataset sizing, sampling investigations and corpus construction will follow.

**[Read Result 002 — Dataset Design and Construction](results/002-data-design/README.md)**

## Reproducing the Experiments

No Magic uses Python with dependencies managed through `pyproject.toml`.

From the experiment directory, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Prepare the dataset:

```powershell
python -m scripts.dataset.download_sources
python -m scripts.dataset.prepare_samples
```

Run the first investigation:

```powershell
python -m scripts.investigations.result_001
```

Alternatively, reproduce the complete preparation and investigation pipeline:

```powershell
python -m scripts.investigations.result_001 --prepare
```

Run the automated tests:

```powershell
python -m unittest discover -s tests -t . -p "test_*.py" -v
```

## Expected Outcome

Reproducible dataset-generation, training and evaluation code, accompanied by short reports covering results, limitations and lessons learned.

High accuracy isn't a requirement. Understanding why an approach works, fails or offers little advantage is equally useful.

## Reference

[FiFTy — File Fragment Type Identification](https://github.com/mittalgovind/fifty) — an existing neural-network approach to file fragment classification.

This is a learning exercise, not a claim of original research.

---

<div align="center">

<img src="../../assets/branding/edgewake-logo.png" alt="Project Edgewake" width="65" />

*Small experiments. Uncertain futures. Useful engineering.*

</div>
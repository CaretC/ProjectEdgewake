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

Known as *file fragment classification*, this is an established problem in digital forensics.

**No Magic** is a practical introduction to machine learning, comparing simple statistical methods, classical ML and small neural networks using ordinary computing hardware.

The aim is to understand dataset preparation, model training and evaluation rather than develop a novel forensic tool.

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

## Expected Outcome

Reproducible dataset-generation, training and evaluation code, accompanied by a short report covering results, limitations and lessons learned.

High accuracy isn't a requirement. Understanding why an approach works, fails or offers little advantage is equally useful.

## Reference

[FiFTy — File Fragment Type Identification](https://github.com/mittalgovind/fifty) — an existing neural-network approach to file fragment classification.

This is a learning exercise, not a claim of original research.

---

<div align="center">

<img src="../../assets/branding/edgewake-logo.png" alt="Project Edgewake" width="65" />

*Small experiments. Uncertain futures. Useful engineering.*

</div>
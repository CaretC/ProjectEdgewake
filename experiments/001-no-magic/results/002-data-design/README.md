<div align="center">

<img src="../../assets/banner.png" alt="No Magic — Experiment 001" width="800" />

# Result 002 — Dataset Design and Construction

**No Magic · Experiment 001**

*Small experiments. Uncertain futures. Useful engineering.*

![Status](https://img.shields.io/badge/status-in%20progress-17A398?style=flat-square)
![Approach](https://img.shields.io/badge/approach-evidence%20led-17A398?style=flat-square)
![Focus](https://img.shields.io/badge/focus-dataset%20design-17A398?style=flat-square)

[← No Magic](../../README.md) · [← Project Edgewake](../../../../README.md)

</div>

---

## About

No Magic is an experiment exploring whether small, locally trained machine learning models can identify file formats from fragments of data without depending on file extensions or initial signatures.

[Result 001 — File Fragment Statistics](../001-fragment-statistics/README.md) examined three simple byte-level measurements: Shannon entropy, printable-byte fraction and zero-byte fraction.

The investigation produced **63 fragments from four individual files**. The text specimen was relatively distinctive, the uncompressed BMP varied considerably between regions, and JPEG and ZIP exhibited similar high-entropy behaviour.

Those were useful observations, but they came from just **one specimen per format**.

A much larger collection of fragments from those same four files would not, by itself, establish that their characteristics are representative of the formats more generally.

Before training a classifier, we need to understand what data would allow us to investigate that question fairly.

This second investigation concerns **the design and construction of that dataset**: the files we choose, what constitutes an independent sample, how we sample their contents, and how we justify the amount and diversity of data we collect.

There is still **no machine learning involved** at this stage.

The intention is to establish a defensible experimental foundation, not merely to accumulate a large number of fragments.

**This Result is in progress.** The sections below establish the question, scope and methodological rationale. Dataset-size analysis, sampling investigations, corpus construction, results and conclusions will be documented as they are carried out.

## Question

**How can we construct a reproducible dataset that supports a credible investigation of file-fragment classification across independent files?**

This follows directly from the question left open by Result 001:

**Do the statistical patterns we observed persist across independent files of each format, or are we mostly learning about the particular specimens we selected?**

To investigate this, we first need to establish:

- Which file formats and variants belong to the problem we are studying.
- Why our fragments have a particular size and sampling position.
- What constitutes an independent source of evidence.
- How much data, and what kinds of data, would support the conclusions we eventually want to draw.

The last of these will be the subject of the next stage of this investigation. We should not select a dataset size simply because it produces a convenient number of fragments.

## 1. Scope and Intended Claim

Our initial objective is to investigate whether a classifier can identify the **source file format** of a **4,096-byte (4 KiB) interior fragment**, without access to the file extension or its initial header.

The four possible labels are:

- `TXT`
- `JPEG`
- `BMP`
- `ZIP`

This is a **closed-set, four-class classification problem**. A future classifier will be asked to choose between these four labels; it will not initially be able to answer "unknown".

We are not yet investigating arbitrary file formats, malicious files, deliberately disguised content or the reliability of full-file identification.

We also need to distinguish the **format of the source file** from the **information visible in one fragment**.

For example, ZIP archives can contain files stored without compression as well as compressed members. A fragment taken from stored text may reveal more about the enclosed text than the ZIP container [4]. Some fragments may not contain enough distinguishing information to identify their source format reliably.

That ambiguity is a characteristic of the problem, not automatically a failure of the classifier.

Eventually, our claims will need to specify the file populations we evaluated, the permitted format variants, the fragment-sampling procedure and whether the source files were independent of those used in model development.

We cannot infer performance on every kind of TXT, JPEG, BMP or ZIP file from a narrow selection of specimens.

## 2. Why These Four Classes?

The four formats were deliberately selected to provide **contrasting byte-level behaviour** while keeping the first classification problem manageable.

This is a *purposive selection*, not a statistically representative sample of all file formats.

File-fragment identification is an established problem in digital forensics. Veenman (2007) investigated classifying disk clusters using statistical features, while Calhoun and Coles (2008) examined methods for predicting the types of fragments taken from within files [1, 2].

That literature motivates the wider investigation; it does **not** establish that our particular four classes are the optimal set.

| Format | Why include it? | Initial hypothesis |
|---|---|---|
| **TXT** | A relatively straightforward reference case for interpreting our original three features. | Ordinary ASCII-compatible text may have a high printable-byte fraction and relatively modest byte entropy. This depends on the kind of text and its encoding. |
| **JPEG** | A compressed image format that challenges simple statistical summaries. | Compressed interior data may have high entropy and resemble other compressed formats when reduced to our three measurements. |
| **BMP** | An image format commonly encountered with uncompressed pixel data, providing a contrast to JPEG. | Entropy, printable bytes and zero-byte frequency may vary considerably with image content, colour depth and the sampled region. |
| **ZIP** | A container format that can hold compressed or stored content of many different kinds. | Compressed regions may resemble JPEG statistically, while stored regions may resemble the files they contain [4]. |

### What we expect to learn

Our initial hypotheses are:

1. **TXT may be comparatively easy to distinguish** within a defined population of ordinary text files.
2. **JPEG and ZIP may be difficult to separate** using only entropy, printable-byte fraction and zero-byte fraction.
3. **BMP may exhibit substantial variation**, both between files and between fragments of the same file.

These expectations are informed by Result 001 and the nature of the formats. They are **hypotheses**, not demonstrated classifier performance.

In particular, Result 001 examined one BMP, one JPEG and one ZIP. We cannot generalise from those specimens alone.

### Scope and variation

Each format includes meaningful variation that could affect what its fragments look like.

| Format | Variation to consider when constructing the dataset |
|---|---|
| TXT | Encoding, language, line endings, natural-language versus structured content |
| JPEG | Image subject, encoder, compression settings and original image provenance |
| BMP | Pixel content, bit depth, row layout and whether the image was derived from another specimen |
| ZIP | Contained file types, compression method, stored entries, archive creation software |

The initial corpus does not have to cover every possible variant. It does need **explicit inclusion and exclusion rules**, with the resulting limitations acknowledged.

We should not quietly remove difficult examples simply because they reduce classification performance.

The selection also gives us a useful connection to published work: the FiFTy project investigates a substantially wider file-fragment classification problem, including 4,096-byte fragments, and provides a reference for eventual comparison [3].

Our **four-class task is not equivalent to FiFTy's 75-class task**. Matching some classes and a fragment length does not make performance scores directly comparable.

## 3. Why 4,096-Byte Interior Fragments?

Result 001 sampled complete **4,096-byte (4 KiB)** fragments.

We will retain that size as the starting point for Result 002 for three reasons.

### An established reference point

Statistical classification of disk clusters and interior file fragments has been studied previously [1, 2].

In particular, the FiFTy project provides models for **512-byte and 4,096-byte** fragments [3]. Working at 4 KiB therefore gives us an established reference size rather than an entirely arbitrary one.

A 4 KiB block is also a familiar unit in storage and forensic contexts, although it is **not a universal physical-sector or filesystem-block size**.

This is justification for adopting 4 KiB as a **baseline**, not evidence that it is the best fragment length.

### Reduced reliance on initial signatures

Our existing sampler excludes the **first 4,096-byte block** and selects complete, aligned blocks from the remaining eligible data.

The purpose is to avoid obtaining an apparently successful classification simply by recognising the file signature or other identifying information at the beginning of a file.

Calhoun and Coles (2008) describe why classification becomes more difficult when a fragment does not include its initial header [1].

This exclusion does **not** guarantee the absence of identifying information. Interior headers, archive structures, repeated signatures and other format-specific patterns may still occur.

The result is a study of **aligned interior fragments**, not every possible arbitrary-offset fragment.

### Continuity with Result 001

Keeping the 4 KiB size unchanged means we can first investigate the influence of source diversity, independence and fragment sampling without changing the amount of data in every fragment at the same time.

Other sizes may be valuable later. For example, 512-byte fragments could expose a different trade-off between available information, classification performance and computational cost.

For now, changing the fragment length would introduce another variable before we understand our starting dataset.

**We are not claiming 4 KiB is optimal.** It is an established, reproducible and manageable baseline that we can challenge in a later controlled investigation.

Likewise, Result 001's maximum of **16 fragments per file** and fixed sampling seed were practical starting choices, not statistically justified optima. The suitability of those settings remains an open question for this Result.

## 4. Independence: Files, Fragments and Related Content

This is the most important distinction established by Result 001.

**63 fragments from four files do not represent 63 independent source files.**

Fragments taken from one file may share statistical characteristics caused by its contents, creator, encoder, structure or other properties specific to that specimen.

If fragments from the same source are used both to train and evaluate a model, we risk measuring its ability to recognise *that specimen* rather than its ability to recognise previously unseen files of the same format.

We therefore need to distinguish several units:

| Term | Meaning in No Magic |
|---|---|
| **Fragment** | A 4 KiB block and the unit a future classifier will predict. |
| **Source file** | The file from which one or more fragments are sampled. |
| **Source-content group** | Files sharing underlying material, such as transformed versions, embedded copies or known near-duplicates. |
| **Dataset partition** | A training, validation or held-out test allocation that must preserve group separation. |

### Why a source-content group matters

Two different filenames do not necessarily represent independent evidence.

For example:

- A BMP converted from a JPEG may have different byte encoding but the same underlying image.
- A ZIP may contain text that also appears as a standalone TXT specimen.
- Multiple resized or recompressed images may originate from one original photograph.

Even when the bytes differ, the shared content may allow a model to learn properties of the common source rather than general format characteristics.

We should track such relationships and assign each source-content group wholly to **one partition** when we later construct training, validation and test datasets.

This principle aligns with group-aware cross-validation methods such as scikit-learn's `GroupKFold`, which prevents samples from the same supplied group being split across folds [5].

However, the library cannot know which files share underlying content. **Defining and verifying those groups is our responsibility.**

### What this means for dataset construction

We will need to retain source provenance, checksums and any known generation or derivation relationships.

Our existing [source manifest](../../data/sources.json) and [generation manifest](../../data/generation.json) provide a useful starting point.

Independence does not mean every file must have been created by a different person or piece of software. It means we need to understand and control important dependencies **relative to the claims we want to make**.

A model might generalise well across files created by one encoder and poorly across entirely different encoders. The design of the dataset determines whether we would notice.

It also follows that collecting *more fragments* and collecting *more independent files* are not interchangeable.

We need to investigate both — and explain why we chose the eventual balance.

---

## Next Steps

The next stage will examine **how much data we need and how we can justify that choice**.

That includes distinguishing the amount of data required to *train* a model from the amount needed to *measure* its performance, examining diversity and sampling behaviour, and investigating whether Result 001's 16-fragment convention is appropriate.

We will document those investigations, their measurements and their conclusions here as we carry them out.

**No new corpus, sampling study or evaluation result is claimed in this document yet.**

## References

1. Calhoun, W. C., & Coles, D. (2008). *Predicting the Types of File Fragments*. **Digital Investigation**, 5(Supplement), S14–S20. [DOI](https://doi.org/10.1016/j.diin.2008.05.005) — Why identification becomes harder when a fragment lacks its original file header.
2. Veenman, C. J. (2007). *Statistical Disk Cluster Classification for File Carving*. **1st International ICST Workshop on Computational Forensics**. [DOI](https://doi.org/10.1109/IAS.2007.75) — Statistical recognition of file types from disk clusters without depending entirely on signatures.
3. Mittal, G., Korus, P., & Memon, N. (2019). *FiFTy: Large-scale File Fragment Type Identification using Neural Networks*. [Paper](https://arxiv.org/abs/1908.06148) · [Project and models](https://github.com/mittalgovind/fifty) — A wider reference problem, including 512-byte and 4,096-byte fragments; eventual benchmark comparisons will require matched protocols.
4. PKWARE. *.ZIP File Format Specification (APPNOTE)*. See the [Library of Congress ZIP format description](https://www.loc.gov/preservation/digital/formats/fdd/fdd000354.shtml) — ZIP archives can contain stored as well as compressed entries; the container does not impose one uniform interior data distribution.
5. scikit-learn. [*GroupKFold — API documentation*](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html) — Non-overlapping source groups during model validation; group identification remains an experimental design task.

---

<div align="center">

<img src="../../assets/icon.png" alt="No Magic" width="64" />

**No Magic · Project Edgewake**

*Ask questions. Measure things. Learn something.*

[↑ Back to No Magic](../../README.md)

</div>

# Task C — Additional targeted verification

Date: 2026-09-20. Status: FACT for cited source contents; CANDIDATE for implications. This is a bounded check of papers already in Task A, not a new literature survey. No dataset downloaded or baseline run.

## TV-01 — Is graph contribution itself an unexplored question?

- Trigger: CA-01/CB-01 contracts require distinguishing a controlled information-value experiment from a routine graph ablation; Task A records ablations but does not settle the exact proposed contrast.
- Primary source: [Eadro author paper, §V-G, Table IV](https://arxiv.org/html/2302.05092), accessed 2026-09-20.
- PRIMARY SOURCE FACT: its graph ablation replaces GAT with an FC layer; other variants remove individual modalities. Therefore generic graph usefulness and generic multimodal usefulness are already tested.
- TASK-C INFERENCE: a defensible empirical contrast must hold node-local evidence, candidate set and evaluation information fixed and test whether observed relations add information beyond capacity/topology nuisance controls. This is a narrower contrast, not proof of world-first novelty. A simple graph on/off result is insufficient.

## TV-02 — Has unseen-failure generalization been studied?

- Trigger: CB-01 proposes scenario-disjoint testing; Task A does not establish whether this is itself new.
- Primary source: [DejaVu author PDF, §5.5 and Figure 15](https://netman.aiops.org/wp-content/uploads/2022/11/DejaVu-paper.pdf), accessed 2026-09-20.
- PRIMARY SOURCE FACT: it compares seen and previously unseen faulty failure units; units combine a location and indicative metric group. Generalization is already an explicit evaluation concern.
- TASK-C INFERENCE: grouped splits are a validity requirement, not standalone novelty. RE2-TT service×fault scenario grouping is not identical to DejaVu's unit definition. Do not claim a new generalization task solely from changing a split.

## TV-03 — Is evidence horizon merely anomaly-boundary sensitivity?

- Trigger: CA-02/CB-02/CC-01 contracts; Task A records BARO detection delay but not whether it is the proposed changing-data-cutoff contrast.
- Primary source: [BARO author paper, §4.8.1–4.8.2](https://arxiv.org/html/2405.09330v1), accessed 2026-09-20.
- PRIMARY SOURCE FACT: §4.8.1 varies assumed anomaly boundary around injection time; §4.8.2 varies method parameters. This establishes prior work on boundary sensitivity.
- TASK-C INFERENCE: fixing a supplied incident boundary while censoring all modalities and graph evidence at the same progressively later cutoff is a different estimand. It can support an incremental retrospective evidence-budget study; it cannot establish real collector arrival latency, autonomous detection or a safe stopping rule. Temporal sensitivity alone is not a new contribution.

## TV-04 — MicroRank exact original contrast

- Trigger: temporal and operation-representation contracts cite MicroRank as close precedent.
- Official artifact identified: [IntelligentDDS/MicroRank](https://github.com/IntelligentDDS/MicroRank), paper file `WWW2021_MicroRank.pdf`.
- Initial web extraction failed. RESOLVED: retrieved official PDF into memory using already-bundled Python 3.12.14 + pypdf; no install and no permanent PDF saved. 1,280,148 bytes; SHA-256 `6d9cd4fcffdecd1dc186750a900ff7c4630b30b53d0173ada8bddb8488954608`; 12 pages. Initial text output encoding failed, UTF-8 retry succeeded. Read §4.2–4.3 and §5.4–5.5 relevant passages, not just abstract.
- PRIMARY SOURCE FACT: §5.4.4/Fig.13 varies number of traces per window; §5.4.3 varies graph weights; §5.5 reports processing overhead by component. Evidence-volume sensitivity, structural ablation and component cost therefore already have precedent.
- PRIMARY SOURCE FACT: §4.2 describes flushing the five-minute detection window after a trigger to avoid repeated detection; §4.3 reads traces in the last windows. This does NOT establish an obligatory five-minute post-alert collection wait. Task-A/reviewer shorthand implying that wait is not used in final Task C. Task A remains untouched; this explicit correction governs Task-C interpretation.
- TASK-C INFERENCE: only the narrower matched-cutoff, shared-candidate, coverage-inclusive comparison of graph value can remain an incremental empirical question. A trace-count sweep or runtime table alone is already covered. No exclusive novelty claim or exact-baseline-reproduction claim is allowed.

## Search boundary

Queries used paper names plus the specific experiment terms (MicroRank window sensitivity, Eadro ablation, DejaVu unseen failures, BARO observation-window/detection delay). Only the above original papers/artifacts enter evidence. Incidental search hits are not added to the literature universe. No third-party summary is used as primary evidence.

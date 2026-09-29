# Independent Task F release assurance

Verdict: **PASS — TASK F RELEASE READY FOR PRE-G REVIEW**  
Review mode: fresh independent, read-only review; reviewer did not author the implementation and received no author recommendation.  
Scope: current local Task F release candidate only; no authority to open final60 or Task G/H/I.

## Blocking findings

- CRITICAL: none.
- MAJOR: none.

## Assurance findings

1. Frozen identity and selections are exact. TD SHA256 is `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`; the manifest hard-locks the selected C1 local/PPR/diffusion configuration, all eight C5 detector thresholds, 256 R chains and the `200 * max(1,E)` proposal budget. Sensitivity and post-hoc findings are not runtime primary rules.
2. E/F equivalence is strong. `f05` records exact matches for all 30 development cases, all eight C5 modes on the predeclared smoke, selected R draws, raw/cache arrays and repeat packets. `f01`–`f03` remain historical attempts; current release evidence is `f04`–`f06`.
3. C1 L/O/R uses one common local vector. R uses deterministic registered seeds, fixed proposal counts, visible self-transition rejections, degree preservation and exact component-partition checks. It makes no spectrum/path/kernel/centrality/mixing claim.
4. C5 preserves G/L/ALL target semantics, TV separation, the `1e-12` fallback, strict event policy and chronological processing. Public triggers invoke past-only TD12-INTEGRATED-MTL; triggers before 360 seconds remain `INSUFFICIENT_HISTORY`. `f04` confirms exact integrated scores and controller-clock-safe packets.
5. Loader admission is byte-bound to recorded Task E loader/replay/integrated-adapter sources and receipts. Model-facing observations/packets project out absolute clocks, paths and trace-key identity.
6. Packets have independent rank and packet hashes, recursive oracle/path firewalling and evidence-reference resolution. Cache identity binds source, TD, code, full configuration, profile and cutoff.
7. Mandatory comparators are preserved. The visible `f05` RCD failure was caused by the wrong interpreter and remains preserved; `f06` passed deterministically in the pinned Python 3.9 runtime.

## Nonblocking limitations and mandatory next-gate controls

- **MAJOR limitation, nonblocking for Task F:** the qualified raw loader is deliberately development-only. Final-scope source ingestion/adapter relationship must be requalified at the separately authorized PRE-G gate without opening final outcomes.
- **MINOR:** RCD is a separately qualified numeric boundary. Final three-seed aggregation, metric-owner first-occurrence mapping, worst-tie padding and evaluator-side scoring remain G-controller responsibilities and must be explicit in the G run contract.
- **MINOR:** packets are tamper-evident serialized dictionaries, not mechanically immutable Python objects. Every consumer must call `validate_packet` before use.
- **MINOR:** the frozen `1e-12` fallback can dominate constant/zero-median channels; Task F correctly preserves and discloses this limitation.
- Historical five-distinct-reviewer certification remains `OPEN / NOT FACTUALLY CERTIFIED`; this single independent Task F assurance does not rewrite that fact.

## Reviewer validation

- Fresh Task F unit/contract run: `65/65 PASS`.
- Current manifest file identity and all 11 pinned source hashes/byte lengths matched.
- No campaign rerun, no final60 material opened, and no file mutation by the reviewer.

## Ruling

Task F satisfies its release contract and is ready for a separately authorized PRE-G validity/freeze review. This verdict does not approve Task G, final60 access, FlashTicket transfer, or any method change.

# TD-v1.2 — Formula/parameter provenance and public compatibility

Owner: Minh; assembled by coordinator 2026-09-26. Class DETAILED_EVIDENCE / FORMATION. Facts are scoped observations; proposed choices remain CANDIDATE. Canonical method: P/docs/research-rca/task-d-method-and-experiment-specification.md. This matrix audits old choices before adjudicating replacements; it does not certify empirical sensitivity or runtime.

## 1. Primary source register actually inspected

| Key | Primary source / artifact | Transfer boundary |
|---|---|---|
| BARO | [Paper §3.4/Algorithm1](https://arxiv.org/html/2405.09330v1) | Robust reference deviation ranking; not whole TD fusion/window/known-boundary detector |
| MR | [MicroRCA official](https://github.com/elastisys/MicroRCA/blob/master/MicroRCA.py) | Reverse-graph PPR mechanism; TD omits host/correlation weighting/driver label shortcuts |
| PR | [PageRank implementation definition](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html) | Mass versus value orientation, damping; not microservice causal theory |
| GDN | [AAAI paper](https://arxiv.org/abs/2106.06947), [official evaluate.py](https://github.com/d-ailin/GDN/blob/9853899da860682669a134e4af315d036aab4eca/evaluate.py) | Graph-conditioned forecasting idea; learned top-k/attention not reproduced. Test-error normalization and report-best test labels forbidden here |
| CIRCA | [KDD paper](https://arxiv.org/abs/2206.05871), [official](https://github.com/NetManAIOps/CIRCA/tree/0215e1880096aa02a305c697f1c23cac4600ebd2) | Conditional-residual reasoning; observed trace graph is not its justified causal model |
| TV | [CDC2019 paper §§II–IV/Eq3](https://web.mit.edu/hamsa/www/pubs/GopalakrishnanLiBalakrishnan_CDC2019.pdf) | Spatial graph variation; binary observed edges, valid-edge mean, max pooling and empirical thresholds are adaptations. No Gaussian bounds transferred |
| RCD | [NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2022/hash/c9fcd02e6445c7dfbad6986abee53d0d-Abstract.html), [RCAEval code](https://github.com/phamquiluan/RCAEval/blob/7600283af1ea5e2e9fff6f07124951d0e989de42/RCAEval/e2e/rcd.py) | Learned metric-graph RCA contextual comparator; task adapter/time-drop/imputation/output pooling not original paper protocol |
| SEL | [Cawley/Talbot2010](https://www.jmlr.org/beta/papers/v11/cawley10a.html), [Bengio/Grandvalet2004](https://jmlr.csail.mit.edu/papers/v5/grandvalet04a.html) | Selection overfitting/CV uncertainty; five development folds do not certify generalization |
| DEP | [Roberts2017](https://www.wsl.ch/lud/biodiversity_events/papers/Roberts_et_al-2017-Ecography.pdf), [Owen2007](https://arxiv.org/abs/0712.1111) | Dependence/blocking concerns; cells/repeats are not independent campaigns |
| SES | [Lakens2017](https://pubmed.ncbi.nlm.nih.gov/28736600/) | Explicit practical-effect bounds; δ=.05 remains study-specific, not adopted utility value |
| RE | [RCAEval paper v3 §3](https://arxiv.org/html/2412.17015v3), [pinned dataset](https://huggingface.co/datasets/phamquiluan/RCAEval/tree/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e) | Release/task facts, not actual-use loader certification |
| LEM | [LEMMA paper v4](https://arxiv.org/html/2406.05375v4), pinned tree/README in JSON | Paper roles differ from physical releases; no assumed traces or GT granularity |

Official source pins checked by reviewer B: RCAEval7600283af1ea5e2e9fff6f07124951d0e989de42; originalRCD373882c6982db7a999ec1ff99ea54c644a48b409; GDN9853899da860682669a134e4af315d036aab4eca; CIRCA0215e1880096aa02a305c697f1c23cac4600ebd2. Availability of a pin is not successful reproduction/license/environment certification.

## 2. Full parameter/formula matrix

Classification names use the user's four categories exactly. A component can contain an adopted primitive plus study-specific application; those are separated, not hidden under one paper citation.

| Component | Formula/parameter | Current TD11 choice | Classification | Primary source/lineage | Why new choice | Alternatives | Selection policy | Sensitivity? | Failure mode | Final proposed status |
|---|---|---|---|---|---|---|---|---|---|---|
| Time bins | C1bin | 10s | STUDY_SPECIFIC_DESIGN | No imported default | Preserve auditable summaries | 5/20s | Fixed10s, dev diagnostics | Mandatory | Sparse bins/smoothing symptoms | Retain, not optimality claim |
| Windows | ref/query | 300/300s | STUDY_SPECIFIC_DESIGN | Known-window task, B geometry | Common bounded evidence | 180/420s | Fixed300/300 | Mandatory | Boundary censoring/transient loss | Retain with actual-use audit |
| Center/scale | median/IQR | robust reference | ADAPTED_FROM_PRIOR_WORK | BARO | Robust reference statistics | mean/SD/residual models | Common reference-only | Floor/tail checks | Constant/heterogeneous channels | Retain principle |
| Numeric quantile | type7 | linear interpolation | STANDARD_STATISTICAL_METHOD | Standard empirical quantiles | Deterministic scalar estimator | Nearest rank | Fixed | Tied/constant fixtures | Small sample instability | Retain explicitly |
| Scale floor | max(IQR,εrel medianabs,1e−12) | .01 relative | STUDY_SPECIFIC_DESIGN | No paper validates exact floor | Prevent zero-IQR division | .0001/.001/.01 | Local registry .001/.01 | Mandatory | Huge deviations/artifact scale | Dev-select, disclose |
| Clip | min(20,r)/20 | cap20 | STUDY_SPECIFIC_DESIGN | None | Avoid silent loss of magnitude | Uncapped/oldcap | Uncapped primary | Oldcap dev comparison | Outlier domination/overflow | Remove primarycap |
| Temporal pool | Q90(query deviation) | Q90 | STUDY_SPECIFIC_DESIGN | No adopted whole formula | Reduce one-bin dominance | max | FixedQ90 | Mandatory | Missing brief faults | Retain candidate |
| Metric channels | max vsQ90 | max | STUDY_SPECIFIC_DESIGN | BARO supports max-deviation idea, not TDpool | Study multiplicity | max/Q90 | Dev absolute L-MRR | Mandatory | Service channel-count bias | Two variants |
| Trace evidence | log1p count | one count channel | STUDY_SPECIFIC_DESIGN | Generic count/log-transform motivation; no inspected primary source establishes adoption of this exact feature | Valid known fields | duration/status pending semantics | Count fixed | Bin/window | Code fault without volume change | Retain bounded count; do not claim prior-work adoption |
| Log evidence | log1p rowcount | LOGCOUNT-v1 | STUDY_SPECIFIC_DESIGN | Available schema, no eventID | Use logs honestly | Templates/semantic fields | No C1log; C5count | MT/MTL | Silent semantic faults/mappingloss | Retain, not contentAD |
| Modality fusion | max/availablemean | fixed(m+t)/2 | STUDY_SPECIFIC_DESIGN | None | Avoid absent-modality discount | fixedmean/max/availablemean | Two local variants | Mandatory | Different available-supportcalibration | Replace fixeddenominator |
| Missingness | masks/availability | zero+fixedweights | STUDY_SPECIFIC_DESIGN | B input facts | Separate unavailable fromhealthy | Imputation rejected forcore | Freeze per-mode | Mandatory masks/duplicates | Selection through finitepredictions | Explicit masks/no targetimputation |
| Raw graph | resolvedsame-traceparent | directed evidence | DIRECTLY_ADOPTED | B physical parent identifiers | Preserve observed orientation | No invented edges | Reference-only | Coverage/horizon | Censored/missingparents | Retain observed≠causal |
| Processing graph | binaryreverse/undirected | undirectedbinary | ADAPTED_FROM_PRIOR_WORK | MR reversegraph, TD binaryprojectioncustom | Test orientation | weighted/casual/learned distinct | Dev6PPRconfigs | Mandatory | Lost semantics/topologyprior | Reopen direction |
| Primary operator | π=(1−d)p+dTᵀπ | rowvaluesmoothing | ADAPTED_FROM_PRIOR_WORK | MR/PR | Grounded mass ranking | Value diffusion | PPR family fixed, OMRRselect | Mandatory | Degree/reachability/centrality | Replace primary |
| Secondary operator | y=(1−α)l/maxl+αPy | q=(1−α)l+αPq | STUDY_SPECIFIC_DESIGN | Standard resolvent walk, not PPR | Operator dependence check | Distinct causal/GNN not mandatory | Threeα secondary | Mandatory | Same-family narrowness | Keep preregisteredbackup |
| Damping | .2/.5/.85 | .5 | STUDY_SPECIFIC_DESIGN | .85 prior reference MR/PR; gridcustom | Bounded search | Larger exploratory sweeps rejected | Dev absolute OMRR | Mandatory | Neighborhood radius/oversmoothing | Dev-select, no finaltune |
| Numeric normalization | max-first p/y | absoluteq tolerance | STANDARD_STATISTICAL_METHOD | Stable linear algebra | Prevent overflow/scale-invalidresidual | Scaledbackward error | Fixed implementation | Huge-evidence fixture | False numerical failures | Explicit stable solver |
| Graph R | directed/undirected switches | undirecteddegree/component | STUDY_SPECIFIC_DESIGN | Structural-control objective, not uniformnull | Keep nuisance degrees/partition | Different nulls distincttasks | Topology-only | Mandatory | Degeneracy/nonuniformity | Redesign exactdirection |
| R count | 256chains | 32 | STUDY_SPECIFIC_DESIGN | Bounded MC precision arithmetic | Smaller simulation error | 32/128/resource amendment | Fixed before final | Actual MCSD/SE | Per-case uncertainty still.03125 | Increase, not sampleN |
| R proposals | 200E | 200E | STUDY_SPECIFIC_DESIGN | No mixingproof | Fixed finitealgorithm | 100/400E | Topology/resource only | Mandatory | Low mobility | Retain with diagnosis |
| Mobility | 32distinct/.8overlap/80%/50% | 16distinct/.8/80%/50% | STUDY_SPECIFIC_DESIGN | Convention not theorem | Informative perturbation check | Reviewed before G | Never outcome-selected | Report all | Graphspace rigidity | Explicit gate |
| C5 mechanism | ridgeforecastresidual | rollingneighborsmoothing | ADAPTED_FROM_PRIOR_WORK | GDN/CIRCA idea only | Model expected dependencybehavior | GNN/TV/smoothing | Forecast primary, TV secondary | Mandatory | Same-type means notpredictive | Material replacement |
| Ridge estimator | meanMSE+λ||β||² | none | STANDARD_STATISTICAL_METHOD | Standard penalized linear regression | Small transparent model | Neural/linearunpenalized | λ3 joint normalforecastloss | Mandatory | Few rows/ill-conditioning | Standard estimator, custom application |
| Neighbor features | own/callee/callerlag+coverage | scoremixing | STUDY_SPECIFIC_DESIGN | Conditionalforecastlineage | Explicit graph restriction | Local/ALL/lag3 | Same nominal5slots | Mandatory capacityrank | Genericcontext vsrelations | G/L/ALL declared |
| Warmup/prefix | 180s=24fit12cal | rolling300ref+60query | STUDY_SPECIFIC_DESIGN | TT geometry, not GDNdefault | Avoid absorbing persistentfault | 10sbin/240sprefix | Fixedclock noτruntime | Mandatory | No independenthealthGT | Replace, fitfirst120only |
| Residual scale | median/IQRfloor.01 | directdeviation | ADAPTED_FROM_PRIOR_WORK | GDN residualnormalization idea | Held-out errors insteadtrainingresiduals | .001/.1 | Caseprefixheldout12 | Mandatory | 9–12correlatederrors noisy | No q99/FPRclaim |
| Shared threshold | weightedCDF q.95/.975/.99 | wholedevmixtureq99 | STUDY_SPECIFIC_DESIGN | Explicit supervisedregimecalibration | Exclude declaredfaultbins intraining | fixedoperatingthreshold | Trainfoldnormals/heldoutmacroF1 | Mandatory | Scored-supportmissingness/proxyGT | Replace, no finaltailfit |
| Streak | 3positivebins | 3×10s | STUDY_SPECIFIC_DESIGN | No sourcevalidates exactduration | Suppress transienttrigger | 1/5 | Fixed3×5s | Eventonly | Delayed/missedfault | Retain value, change duration |
| Refractory | 300s | 300s | STUDY_SPECIFIC_DESIGN | Demo policy not SLA | Avoid repeatedtriggers | 60/600 | Fixed | Eventonly | Suppresses secondincident | Retain boundedreplay |
| TV | meanedges(z_u−z_v)² | absent | ADAPTED_FROM_PRIOR_WORK | TV paper Eq3 sum | Distinct spatialmechanism | sum/correlationweights | Secondary fixedgeometry | Commonmode/masks | Isolates/equalshiftblind | Add preregistered, not RCAbackup |
| Local selection | absoluteL-MRR | no labeltune | STUDY_SPECIFIC_DESIGN | SEL warnsselectionbias | Avoid weakcontrolforgain | Jointlocal/graph objective | Eight bounded configs | Leavecellwinners/margins | Conditional representation bias | New permission, not proofoptimal |
| Grouped folds | 5folds/2cells | no outcome selection | STUDY_SPECIFIC_DESIGN | DEP blocking principle | Keep repeats together | Leavecell/nested costly | Exactfoldlist beforeoutcomes | Mandatory instability | Only10cells/unbalanced | Adopt boundedprocess |
| Ranking metrics | expectedtieRR/Hit/NDCG | same endpoints | STANDARD_STATISTICAL_METHOD | Ranking definitions/uniformtieexpectation | Do not name-sortwin | Strict ranks falselyprecise | Fixed MRRprimary | Fixtures | WrongGT/missingtarget | Retain |
| Practical effect | δ=.05 | .05 | STUDY_SPECIFIC_DESIGN | SES principle not exactvalue | Declared practicalcriterion | No postoutcomechange | Fixed | Precisionplanning | Underpowered/utilitygap | Retain with illustration |
| Bootstrap | pairedcells50k/97.5%each | samefamily2 | STANDARD_STATISTICAL_METHOD | Bootstrap/Bonferroni principle | Conditional resamplingsensitivity | IIDtests rejected | Fixed20cells,two contrasts | Root/faultleaveouts | Sharedcampaignnotrepaired | Retain narrow interpretation |
| RCD params | bins5,gamma5,alphaconst | literatureonly | DIRECTLY_ADOPTED | Pinned RCAEvalartifact | Runnable graph-family comparison | OriginalbinsNone notsame | Fixeddefaults, three seeds | bins3/7dev | Env/CI assumptions | Mandatorycontext |
| RCD adapter | time-drop/1s/missing/pool | absent | STUDY_SPECIFIC_DESIGN | Exactwrapper discrepancy | Compatible TD service target | Different wrapperpatch | Fixed before final | Time/F-node/partialtiefixtures | Timeleak/worsttiepaddedoutputs | Explicit adaptation not replication |

All STUDY_SPECIFIC_DESIGN rows inherit their corresponding D section's input assumptions, failure-attribution tree, registered alternatives/sensitivity/backup and claim restrictions. They remain candidates pending human review; empirical sensitivity status is **NOT RUN**, not omitted or passed.

## 3. Dataset compatibility facts and roles

[Machine receipt](td-v1.2-public-metadata.json), [bounded script](audit_td_v1_2_public_metadata.py). RE3TT90footerobjects:6,026,998bytes; rows M54,030/L1,627,863/T4,152,676; M21schema variants/L1/T1; allcounts matchmetadata. Per-file receipt has206/rangebytes/footerhash/officialLFSidentity/timeextrema/schema; no telemetry row read. This repeats the reviewer's bounded footer check to produce a persistent complete receipt, not raw acquisition.

| Release | GT/modality/graph facts | Scientific role / method | Timing/joins/exposure and admission |
|---|---|---|---|
| RE2-TT90 | Service-root/fault/inject;M90/T90/L89;observed parents fulltraceaudit | C1primary/C5regimeproxy/BARO/RCD | Beforedeclared injection720s; exactwindow/prefix/root/joins all-used future;historical outcomes exposed |
| RE3-TT30 | SameGT;2roots/8cells/repeats3–6;allM/L/T;codefaults | Frozen30-case fault-family transfer;equalcellmean;no labeltuning | Prefix beforedeclared900s;sampleone raw geometry;29rawjoinsunknown;numericRE2thresholds frozen |
| RE3-OB30 | Fourroots/10cells×3;allM/L/T | Cross-application codefault portability candidate | Exactliteralaliases/units/clock/window/prefix not certified bymetadata;noTTpooling |
| RE2-OB90 | Five roots×six faults×3;allM/L/T | Optional resource/network externalcontrol | Two faultyhorizons210/284s;cannotquietly shorten onlyhardcases;onefrontendidentity mismatch needs evidence |
| RE2-SS90 | M/L,noT | LocalM/L+BARO/RCDcomponentportability | No observedtracegraph; service identity/root windows admission remains |
| RE3-SS30 | M/L,noT;three roots/ninecells;answerfiles8 | Codefault local/learnedmetricgraph task | No fabricatedtraceedges;answerfiles blocked;no allcells3assumption |
| RE1-SS125 | Metric-only | Compatibility/literature role | Not tri-modal/tracegraph |
| LEMMA ProductReview20211203 candidate | Physicalpreprocessed M/Lzips;entityGT/time meaningful only afterPPTXaudit | Entityranking/longtime local-modality portability;learnedgraph would be distincttask | Exactpod/servicegranularity/cardinality OPEN;faulttimesJST telemetryUTC−9h;source-license discrepancy unresolved |
| LEMMA Cloud | SixM/fiveLzips;20240207CloudTrail-only;no separatelylistedT | Componentcandidate, nottrace-C1replication | EKSlogabsence/crossmodalitymapping/GT OPEN;no automaticpaper-version counts |

LEMMA immutablepins/READMEsha/filetrees included machineJSON: ProductReviewPreprocessed df25484004e50483de6f6756c3a4d7ab03174b83;CloudPreprocessed03f82a2c4b16afe09e9315def9f5d6990427000a;ProductOriginal63aa4abe7dd7217d9b0b108894c7d893e2b29aef;CloudOriginal9e5ad23fa390f6b596f41be014233fe446679bcd. Productpreprocessed total~6.655GB;Cloud~4.738GB, not downloaded. Card/body cc-by-nc/cc-by-nd discrepancy is OPEN, not guessed.

RE3TT cells:auth f1/f2/f3 each4,f4=3;route f1/f2/f4 each3,f3=6. Equalcellweight differs fromcasemean:route/f3=.125versus.20. RE3 does not become independent-campaign or unseen-service evidence; roots also appear inRE2.

Local raw RE3route/f2_1 sample:183,623tracerows;27services;55wholecaseresolvedcrossservice relationtypes;8,398temporalcontainmentfailures;74,449logrows/48containers/23exacttrace-servicematches;68metricentities,3.7767%metriccellmissingness.300sreference/query:35,441/22,245trace rows,54refrelationtypes,34,996/34,996referenceparentresolution,root visible,300metricrows/side,13,564/9,152logrows. These reviewer read-only checks support feasibility only this case. Existing raw manifests and B evidence own physical sample hashes; no new sample created.

No RE2/RE3 TT affected-node/operation/path/onset GT. System-bin injection-regime agreement is a proxy, not node anomalyF1 or productionFPR. Actual arrival unavailable; H independent healthy/fault/availability evidence required. Count-only RE3 signal weakness is a hypothesis, not demonstrated failure or permission to add semantic features after outcomes.

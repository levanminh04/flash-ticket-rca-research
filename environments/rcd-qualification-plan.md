# RCD isolated runtime qualification recipe

State: CANDIDATE execution recipe, prepared without installing an environment or executing numeric fixtures. This file does not assert a successful runtime or comparator result. Owner: Task E coordinator. Authority: canonical TD-v1.3 §6/8 and U27R scoped development permission. C5 amendment review and fixture/resume gate must pass before installation/execution. These three preparation files do not change the scientific method or any decision state.

## Sources and exact adaptation

Reuse `baselines/task-e-source-manifest.json` and its pinned RCAEval revision `7600283af1ea5e2e9fff6f07124951d0e989de42`; original RCD lineage is `373882c6982db7a999ec1ff99ea54c644a48b409`. Retain all upstream bytes. The loader checks the manifest against the coordinator's pre-run hash and verifies each relevant source. It verifies the original wrapper SHA256 `e6a7df13e4f3256b45da0713b07b6bf41fb9178333e31397701ab2f08872f628`, patch SHA256 `472685d2513a47cefce36640d9de3e21769923f85de48f7cf6feec43e2ae8838`, patched wrapper SHA256 `036946005d53e5c6a11e2a4b5c099f2194ab104f15df8fd74d74668827278393`, and the exact two-line delta. The delta drops `time` from normal/anomalous frames immediately after the known-window split. It does not change CI, discretization, chunking, alpha progression, seed handling, or ranking.

Load only the bare `RCAEval/e2e/rcd_td12.py` with its pinned `RCAEval/io/time_series.py` dependency, using temporary empty package namespaces. The RCAEval framework `__init__` and its exception-to-ranking decorator are never imported. No arbitrary installed RCAEval or alternate method is a fallback. Import warning suppression is contained with `warnings.catch_warnings`; diagnostic warnings remain visible during execution. No source is rewritten for this import behavior.

Stock `causal-learn==0.1.2.3` is insufficient. The [official pinned setup](https://github.com/phamquiluan/RCAEval/blob/7600283af1ea5e2e9fff6f07124951d0e989de42/docs/SETUP.md) and [link script](https://github.com/phamquiluan/RCAEval/blob/7600283af1ea5e2e9fff6f07124951d0e989de42/script/link.sh) require four customized files. The Windows recipe copies their exact bytes into only this isolated environment, equivalent to the official source links:

| Installed path under `causallearn/` | Required source SHA256 |
|---|---|
| `utils/PCUtils/SkeletonDiscovery.py` | `96b65269d34c89f1eb750eec7adf56c07f56404acf02594faa6d2fa40bc8e3c4` |
| `graph/GraphClass.py` | `1d75e73450d635a89c929b67e88644d6b9a175a560c25a24294cd99944f54635` |
| `utils/Fas.py` | `4f7e07434dc09e8335cfecdf5ad340d24fe57530daa0bf0bb0d2eaaa5520ddb5` |
| `search/ConstraintBased/FCI.py` | `8b4acd094cdc1d83b4e15a3c1408a3817209000294c0124b464c2a00c944e54a` |

The localized RCD path uses the first two; all four are checked to preserve the official installation contract. `pyAgrum/lib/image.py` in the same link script supports unused plotting/other algorithm paths; this bare RCD source and its imports do not use pyAgrum. No Java, torch, DVC, PyRCA, or whole RCAEval installation is required by this qualified path. Installed metadata/import checks remain necessary before declaring that the dependency closure works.

## Dependency closure and platform delta

Use existing `C:/Users/84583/AppData/Local/Programs/Python/Python39/python.exe` to create `environments/task-e/rcd39`. Python3.9 on Windows differs from the official Ubuntu/Python3.8 recipe and must be disclosed. It is a compatibility qualification of the TD adapter, not exact environment reproduction. The loader rejects other interpreter minor versions or environment locations and rejects any pre-imported causal-learn/RCAEval modules.

The exact runtime pins are executable constants in `scripts/task_e/rcd_runtime.py::PINNED_PACKAGES`. Most are copied from the pinned RCAEval `requirements_rcd.lock`: numpy1.23.5, pandas2.0.1, scipy1.10.1, scikit-learn1.2.2, causal-learn0.1.2.3, networkx2.5, tqdm4.65.0 and their metadata/import dependencies. The [causal-learn PyPI version metadata](https://pypi.org/pypi/causal-learn/0.1.2.3/json) declares numpy, scipy, scikit-learn, graphviz, statsmodels, pandas, matplotlib, networkx, pydot and tqdm. Statsmodels0.14.0/patsy0.5.3 satisfy its declared closure even if unused by localized RCD.

Explicit compatibility additions not present in the RCAEval lock: matplotlib3.7.1, importlib-resources5.12.0, zipp3.15.0. Matplotlib is imported by the exact source but is missing from that lock; the original RCD requirements instead used matplotlib3.3.4. The chosen version has a Windows Python3.9 wheel. These are candidate environment choices, not undocumented source-method changes. Preserve a complete `pip freeze --all`, `pip check`, installer output/report and exact Python patch version in the execution receipt. If resolution/imports fail, preserve the attempt and fix the execution recipe explicitly; do not change the algorithm or silently loosen pins.

## License evidence and limitation

The local pinned RCAEval `LICENSES/LICENSE-RCD` and `lib/causallearn/LICENSE` both contain the cmu-phil 2022 MIT notice, SHA256 `9e71f9277846b06991c7121d015186cc21e155c3bc521ec4287fe085ea07da29`. Keep that notice with all copies and derived distribution. This is the license notice shipped by the authoritative RCAEval source for this runtime.

Read-only inspection of the [original RCD pinned tree](https://api.github.com/repos/azamikram/rcd/git/trees/373882c6982db7a999ec1ff99ea54c644a48b409?recursive=1) found `LICENSE-causal-learn`, `LICENSE-pyAgrum` and their nested copies; no top-level `LICENSE`. [LICENSE-causal-learn](https://github.com/azamikram/rcd/blob/373882c6982db7a999ec1ff99ea54c644a48b409/LICENSE-causal-learn) is the same cmu-phil MIT notice. Do not describe this as independently verified MIT licensing of all original RCD algorithm code. The absence of a separate original-algorithm notice is a disclosed provenance limitation; root coordinator owns the interpretation for any later redistribution. This qualification copies only the already pinned RCAEval source path and does not import the original RCD repository.

## Coordinator commands, after resume gate

The coordinator must create an immutable environment-preparation run contract and preserve stdout/stderr BEFORE these commands, then capture freeze/check/file-hash receipts. Do not execute these commands from a pending-gate preparation task. Every retry uses a new run ID. PowerShell paths below are literal and the only installation target is the named isolated environment.

```powershell
Set-Location -LiteralPath 'D:/Project/flash-ticket-rca-research'
& 'C:/Users/84583/AppData/Local/Programs/Python/Python39/python.exe' -m venv 'environments/task-e/rcd39'
$rcdPython = 'D:/Project/flash-ticket-rca-research/environments/task-e/rcd39/Scripts/python.exe'
# Pin packaging tools separately and retain their versions/installer output.
& $rcdPython -m pip install 'pip==25.2' 'setuptools==68.2.2' 'wheel==0.41.3'
# Importing this preparation module uses only stdlib; this emits exact pins.
$rcdPins = & $rcdPython -c 'from scripts.task_e.rcd_runtime import PINNED_PACKAGES; print("\n".join(k+"=="+v for k,v in PINNED_PACKAGES.items()))'
& $rcdPython -m pip install @rcdPins
$rcdSource = 'D:/Project/flash-ticket-rca-research/baselines/upstream/rcaeval-7600283af1ea5e2e9fff6f07124951d0e989de42/lib/causallearn'
$rcdTarget = 'D:/Project/flash-ticket-rca-research/environments/task-e/rcd39/Lib/site-packages/causallearn'
$rcdFiles = @('utils/PCUtils/SkeletonDiscovery.py', 'graph/GraphClass.py', 'utils/Fas.py', 'search/ConstraintBased/FCI.py')
foreach ($relative in $rcdFiles) {
    Copy-Item -LiteralPath (Join-Path $rcdSource $relative) -Destination (Join-Path $rcdTarget $relative)
}
& $rcdPython -m pip check
& $rcdPython -m pip freeze --all
```

Before the fixture, the coordinator calls existing `scripts.task_e.contract.begin_run` with:

- `command`: `[absolute_rcd39_python, absolute_test_rcd_runtime_py, absolute_new_run_directory]`;
- source files including `rcd_runtime.py`, `comparators.py`, `ranking.py`, `test_rcd_runtime.py`, `contract.py`, this recipe, the source manifest, patch and all pinned sources above;
- config `rcd_runtime_qualification_authorized: true` only after the resume gate;
- config `rcd_source_manifest_sha256` equal to the current manifest's SHA256;
- synthetic-only exposure; seeds420/421/422 and bins3/5/7; no corpus inputs;
- references to the resume, environment-install, `pip check`, freeze and customization receipts.

Then execute the recorded command with stdout/stderr redirected to that new run directory. Existing generic `run_stage.py` does not supply this specialized config flag/manifest pin; use `begin_run` directly or an explicit reviewed launcher update. Never invent a dummy contract to bypass the gate.

```powershell
# NEW_RUN_DIRECTORY must already contain the coordinator's complete contract.
& $rcdPython 'D:/Project/flash-ticket-rca-research/tests/task_e/test_rcd_runtime.py' 'NEW_RUN_DIRECTORY'
```

## Actual CI fixture and acceptance meaning

`test_rcd_runtime.py` runs the exact bare wrapper through existing `comparators.rcd_run`. Six opaque metrics and a required relative `time=0..599` column exercise gamma5 chunking. Both halves are exact repeats for five controls; one metric has a +30 separated-support shift. For each seed420/421/422 and bins3/5/7, run twice sequentially. The specified rank is the single shifted metric; repeated halves remain exactly independent of the F indicator after common discretization. Repeat output and complete observed CI sequences must agree. This is deterministic fixture evidence, not development efficacy or a seed winner.

The observer wraps actual `CausalGraph.ci_test`, records labels, actual matrix shape/hash, conditioning indices and returned p-values, and calls the original method unchanged. It asserts `time` never appears at that CI boundary, only allowed metric keys and last-column F appear, there are600 rows, F has the expected two halves, the real chi-square/discrete path is active, and p-values are finite. It deliberately does not replace `CI_TEST`, because upstream identity comparisons select discrete cardinality handling. At least one actual CI call is mandatory per execution. Rankings also exclude time/unknown keys.

A real identical-halves run must return successful empty ranks. A separately named deliberate exception at the reached real CI boundary must return explicit `FAILURE/upstream_exception`, with `ranks=None`; it cannot become successful empty ranks or dummy ranks. All attempts, per-seed/bin results and CI records are retained in `rcd-fixture-report.json`. Qualification passes only when all tests and environment/source checks pass. A failed/import-incompatible attempt is retained and interpreted as execution failure pending correction; an irreducible method/dependency incompatibility returns to Task D as §6 requires.

Remaining scope outside these files: coordinator source/license receipt persistence, actual installation/qualification, raw1s eligibility and reference-median imputation, exact owner mapping and service first-occurrence/worst-tie padding, per-seed averaging/failure0, development outcome/sensitivity runs. This preparation does not claim those checks have happened. No final or development dataset is downloaded by the loader or fixture.

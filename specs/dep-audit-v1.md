# Job template dep-audit-v1: Python dependency audit

DRAFT for Nitya to correct (task 5). The owner fixes this once, when the job
type is set up; the agent that stalls never writes its own "done" criteria.
The auditor's prompt is built from this file, and `rebbi/verify.py` checks
reports against `answer-key-sqlite-utils-3.38.json`.

## What the report must contain

Seven sections, each a level-2 heading numbered exactly as below, then a JSON
appendix. Facts come only from files in the repository at the pinned commit.

1. **Scope.** Repository, commit, and the manifest files read.
2. **Runtime dependencies.** Every `install_requires` entry with its version constraint, written exactly as declared (empty if none).
3. **Optional dependency groups.** Every `extras_require` group and the packages in it.
4. **Where runtime dependencies are used.** For each runtime dependency, every file in the package that imports it.
5. **Unused and undeclared.** Runtime dependencies that no file imports; third-party modules the package imports but declares nowhere (neither runtime nor optional), with the files and whether each import is optional (inside `try` / `except ImportError`).
6. **Version pinning.** Runtime dependencies with no version constraint at all.
7. **Risks and recommendations.** At least one recommendation tied to a finding above.

End the report with one fenced `json` block holding the same facts:

```json
{
  "runtime_dependencies": [{"name": "click-default-group", "constraint": ">=1.2.3"}],
  "optional_groups": {"test": ["pytest"]},
  "imports": {"click": ["sqlite_utils/cli.py"]},
  "unused_dependencies": [],
  "undeclared_imports": [{"module": "numpy", "files": ["sqlite_utils/db.py"], "optional": true}],
  "unpinned": ["click"]
}
```

Package names are lower-case distribution names as declared (`python-dateutil`,
not `dateutil`). File paths are relative to the repository root, with `/`.

## Pass criteria (the verifier fails closed)

| Check | Passes when |
| --- | --- |
| Structure | All seven numbered sections are present and not empty, and the JSON block parses |
| Runtime dependencies | Same names and constraints as the key |
| Optional groups | Same groups, same packages in each |
| Imports | For every runtime dependency, the same set of files as the key |
| Unused | Same list as the key (empty for sqlite-utils 3.38) |
| Undeclared | Same modules, files and optional flags as the key |
| Unpinned | Same list as the key |

Any missing section, unparsable JSON or wrong value is a FAIL. A report that
stops early (the baseline run) fails on structure.

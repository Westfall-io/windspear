# Windspear — README for Git-driven SysML ingestion

## Overview
- **Purpose:** Ingest SysML models embedded in Jupyter notebooks from a git repository, execute SysML cells to export element metadata, parse requirements/verifications/actions, store results in a PostgreSQL database, and notify a webhook when processing completes.

## High-level flow
- **Checkout repo:** clone the target repository and switch to the branch/commit referenced by the webhook.
- **Extract models:** scan notebooks for SysML cells, assemble a temporary notebook, execute it using the SysML kernel (via `papermill`) to export element JSON.
- **Parse & map:** convert exported element JSON into internal dictionaries of models and elements; parse requirements, verifications and actions and collect tool metadata (container/artifact URIs and variables).
- **Persist:** insert commit, model, element, requirement, verification and action records into a PostgreSQL database using SQLAlchemy ORM.
- **Notify:** mark commit processed and POST a small payload to the configured webhook endpoint.

## Key files / modules
- **`src/main.py`:** Entry point. Orchestrates the end-to-end processing of a single commit/ref. Uses `fire.Fire(main)` so it can be run from the command line. Calls into `gitrepo`, `notebook` and `database` modules and posts to the `WINDSTORMHOST` webhook when done.
- **`src/env.py`:** Environment defaults and configuration keys. Important environment variables: `DEBUG`, `SQLHOST`, `DBUSER`, `DBPASS`, `DBTABLE`, `GITHOST`, `GITUSER`, `GITPASS`, `APIHOST`, `WINDSTORMHOST`, `HARBORTOOL`, `ARTIFACTSTOOL`.
- **`src/gitrepo/methods.py`:** Clones the repository, finds the directory name, switches to the branch and checks out the commit; builds a short commit history used to find commit dates.
- **`src/notebook/methods.py`:** Core logic to:
  - discover `.ipynb` files with SysML kernels;
  - extract SysML code cells and build a temporary notebook;
  - execute the temporary notebook with the SysML kernel via `papermill` so model exports appear in outputs;
  - decode exported element JSON (base64-encoded inside HTML output) and build `models` and `elements` dictionaries;
  - parse models into `requirements`, `verifications`, and `actions`, collecting tool metadata (harbor/artifacts URIs and variables).
- **`src/notebook/jupyter.py`, `src/notebook/action.py`, `src/notebook/sysml.py`:** Helper modules used by `notebook.methods` (notebook construction, SysML-specific helpers, and action storage helpers).
- **`src/database/models.py`:** SQLAlchemy ORM table definitions for `model_repo`, `commits`, `models`, `elements`, `models_elements`, `requirements`, `verifications`, and `actions`.
- **`src/database/methods.py`:** Database access layer. Important functions:
  - `connect()` — create DB engine/connection using values from `env.py`;
  - `insert_commit_data()` — ensure repo row exists, insert or reset commit record; clears previous rows for the commit when re-processing;
  - `insert_model_data()` — insert elements and models and create linking rows in `models_elements`;
  - `insert_req_ver_actions()` — insert requirements, verifications and actions (including tool URIs, variables and dependencies);
  - `push_commit_completed()` — mark commit processed/complete.
- **`src/models.py`:** Local model helper classes for verifications, actions and tool execution metadata used by higher-level parsing (not the DB models).

## Database schema (summary)
- `model_repo` — tracked repositories and default branch.
- `commits` — one row per processed commit (`ref`, `commit`, `processed`, `date`).
- `elements` — exported SysML elements JSON and element ids.
- `models` — extracted SysML models (nb_id, execution order, model text and hashes, element name).
- `models_elements` — many-to-many linking models ↔ elements for a commit.
- `requirements`, `verifications`, `actions` — parsed artifacts from elements with links back to `elements` and `commits`.

## Runtime / prerequisites
- Python packages (from `requirements.txt`): notable packages include `papermill`, `gitpython`, `sqlalchemy`, `requests`, `python-dateutil`, and Jupyter kernels/plugins for SysML (and `sos` if used).
- A PostgreSQL instance reachable at `SQLHOST` with a database name `DBTABLE` and user credentials `DBUSER`/`DBPASS`.
- A SysML kernel and its notebook export features available so that executing the temporary notebook produces the expected exports (see comments in `src/main.py` about `sos_notebook` and `jupyterlab-sysml`).

## Running
- Minimal CLI example (fire-based):

```
python src/main.py --ref=refs/heads/main --commit=<commit_sha> --repopath=gitea_admin/test_workflow --default_branch=main
```

- You can also run via `python -m src.main` if your `PYTHONPATH` includes the project root.

## Debugging tips
- Set `DEBUG` environment variable to enable temporary output and additional files.
- If the SysML kernel does not start, the code retries a few times; inspect logs from `papermill` and kernel installations.
- Database integrity errors are raised when expected element/requirement rows are missing — inspect inserted `elements` JSON to verify exported content.

## Next steps / notes
- The repository expects SysML-specific notebook outputs (base64-encoded JSON inside HTML). If exports change, update `notebook.methods` decoding logic.
- Consider adding unit tests for parsing logic in `src/notebook/methods.py` and for DB persistence functions.

If you'd like, I can: run a static pass over additional helper files, add examples, or adjust the README to match a preferred style.

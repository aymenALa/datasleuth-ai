# DataSleuth AI

DataSleuth AI is a small portfolio project for investigating data quality issues
in CSV datasets. It is intended to use Pandas for analysis, Streamlit for the
interface, Groq for optional language-model coordination, and Pytest for tests.

## V1 scope

The planned V1 workflow will inspect a CSV, run predefined analytical tools,
verify findings, and recommend cleaning actions without modifying the dataset.

Implemented in Task 02:

- CSV ingestion from file paths and uploaded binary file-like objects
- UTF-8 and UTF-8-with-BOM support
- File-size, row-count, column-count, and column-name validation
- Application-specific errors for empty, malformed, duplicate-column, invalid-
  encoding, and oversized CSV input
- A `DatasetContext` contract containing the validated DataFrame and metadata

Header-only CSV files are intentionally accepted: they produce a valid
`DatasetContext` with zero rows and the declared columns. Empty or
whitespace-only files are rejected.

Implemented in Task 03:

- Deterministic dataset profiling, missing-value analysis, duplicate detection,
  column inspection, and IQR outlier candidate detection
- Compact `ToolResult` outputs with bounded evidence and JSON-compatible values
- Read-only analysis that never modifies the input DataFrame

The tools report statistical observations only. Outlier candidates are not
confirmed data-quality errors, and no domain-specific validity rules or
automatic cleaning are applied.

Implemented in Task 04:

- A single bounded Groq investigation agent with dynamic selection of the five
  deterministic tools
- Explicit JSON tool schemas and an allowlisted local dispatcher
- Structured investigation state, steps, observations, usage, and completion
  status
- Retry-bounded Groq requests with missing-key, rate-limit, and network errors

Configure `GROQ_API_KEY` in the environment to use the agent. Unit tests use
mocked clients and do not require credentials. The agent does not execute
model-generated Python or shell commands, modify datasets, or apply cleaning.

Still planned: formal report validation/export and the Streamlit workflow.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
Copy-Item .env.example .env
```

Add a Groq API key to `.env` to run the optional investigation agent.
Do not commit `.env` or real credentials.

## Current checks

```powershell
python -c "import datasleuth"
pytest
```

## Planned features

- CSV loading and basic data-quality profiling
- Deterministic analytical tools
- Verified findings and explainable cleaning recommendations
- Optional Groq-assisted investigation coordination
- Streamlit workflow and focused Pytest coverage

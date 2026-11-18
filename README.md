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

Implemented in Task 05A:

- Deterministic validation of tool observations and numerical finding claims
- Evidence-backed finding classifications for measured facts and statistical
  candidates
- Conservative cleaning recommendations that never modify the dataset
- Strict JSON and escaped Markdown investigation reports
- Explicit outcomes for verified findings, no issues in executed checks,
  incomplete investigations, and failed investigations

Implemented in Task 05B:

- Local Streamlit interface for CSV upload, bounded preview, and Pandas-inferred
  schema overview
- Explicit investigation controls with session-state persistence and stale
  result invalidation when the uploaded dataset changes
- Readable investigation trace, verified findings, recommendations, warnings,
  and unverified model interpretation sections
- Strict JSON and Markdown report downloads

The interface never modifies the source CSV and does not execute cleaning.

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

## Run the Streamlit application

```powershell
streamlit run app.py
```

Upload a CSV, review the bounded dataset overview, enter an investigation goal,
and click **Run investigation**. Groq is called only after that explicit action.
The app requires `GROQ_API_KEY` in the process environment and never displays
the credential.

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
- Streamlit workflow refinements and focused Pytest coverage

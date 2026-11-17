# DataSleuth AI

DataSleuth AI is a small portfolio project for investigating data quality issues
in CSV datasets. It is intended to use Pandas for analysis, Streamlit for the
interface, Groq for optional language-model coordination, and Pytest for tests.

## V1 scope

The planned V1 workflow will inspect a CSV, run predefined analytical tools,
verify findings, and recommend cleaning actions without modifying the dataset.

This repository currently contains initial scaffolding only. CSV analysis, the
Groq integration, the investigation agent, validation, reports, and feature
tests are not implemented yet.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
Copy-Item .env.example .env
```

Add a Groq API key to `.env` only when the future Groq integration is implemented.
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

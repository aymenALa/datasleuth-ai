# DataSleuth AI architecture

## V1 outline

1. `app.py` provides the local Streamlit interface for upload, overview,
   explicit investigation, trace, findings, recommendations, and report export.
2. `data_loader.py` will load CSV input into Pandas structures.
3. `tools.py` contains five predefined, deterministic analyses: dataset
   profiling, missing-value analysis, duplicate detection, column inspection,
   and conservative IQR outlier candidate detection.
4. `agent.py` coordinates bounded investigations through the available tools.
5. `groq_client.py` provides the optional Groq API boundary.
6. `validator.py` will verify proposed findings.
7. `reports.py` will format findings and cleaning recommendations.
8. `models.py` will hold shared domain models, where needed.
9. `config.py` will centralize environment-backed configuration.

Tool functions operate on the validated `DatasetContext` and return compact
`ToolResult` objects suitable for future agent tool calling. Their outputs use
Pandas-inferred types and parsing semantics; they do not establish domain
validity. In particular, IQR results are statistical outlier candidates rather
than confirmed errors. Evidence is bounded and no tool mutates the source
DataFrame.

The Task 04 agent uses `GroqClient` with model `openai/gpt-oss-20b` by default.
It sends a compact dataset overview, exposes exactly the five allowlisted tools,
executes calls locally, and returns tool results to the model in the required
assistant/tool message order. The loop is limited to 8 model turns and 8 tool
calls, detects repeated calls, bounds Groq retries, and records available token
usage. CSV cell contents are treated as untrusted data rather than instructions.

`InvestigationState`, `InvestigationStep`, and `InvestigationResult` provide a
lightweight trace for a future UI. The agent reports incomplete investigations
explicitly; model interpretations remain separate from tool observations.

Task 05A adds deterministic validation in `validator.py` and bounded report
generation in `reports.py`. Numerical findings must resolve to metrics from a
successful executed tool step; model summaries are retained as unverified
interpretations. Recommendations identify the issue, affected columns,
supporting evidence, action, and human-review risks. JSON exports reject
non-finite values and Markdown exports escape untrusted text. Reports
distinguish issues found, no issue found in executed checks, incomplete
investigations, and failed investigations.

The Streamlit layer stores only the current dataset context, content signature,
investigation result, and generated report in `st.session_state`. Uploading a
different byte signature clears stale results. It invokes the existing agent
only from the explicit Run Investigation button, sends no full dataset to
Groq, and uses bounded previews/evidence. Downloaded JSON is strict and the
Markdown renderer escapes untrusted text.

Long-term storage, authentication, deployment, automatic cleaning, and further
UI work are not implemented.

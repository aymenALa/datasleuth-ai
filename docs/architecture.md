# DataSleuth AI architecture

## V1 outline

1. `app.py` will provide the Streamlit interface.
2. `data_loader.py` will load CSV input into Pandas structures.
3. `tools.py` contains five predefined, deterministic analyses: dataset
   profiling, missing-value analysis, duplicate detection, column inspection,
   and conservative IQR outlier candidate detection.
4. `agent.py` will coordinate investigations through the available tools.
5. `groq_client.py` will provide the optional Groq API boundary.
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

The agent, Groq integration, cleaning recommendations, finding validation,
reports, and Streamlit workflow are not implemented yet.

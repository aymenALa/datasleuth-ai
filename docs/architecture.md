# DataSleuth AI architecture

## V1 outline

1. `app.py` will provide the Streamlit interface.
2. `data_loader.py` will load CSV input into Pandas structures.
3. `tools.py` will contain predefined, deterministic data-quality analyses.
4. `agent.py` will coordinate investigations through the available tools.
5. `groq_client.py` will provide the optional Groq API boundary.
6. `validator.py` will verify proposed findings.
7. `reports.py` will format findings and cleaning recommendations.
8. `models.py` will hold shared domain models, where needed.
9. `config.py` will centralize environment-backed configuration.

The assistant will recommend cleaning actions without modifying the source CSV.
The investigation workflow and Groq integration are not implemented yet.

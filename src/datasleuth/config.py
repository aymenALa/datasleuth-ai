"""Small, application-wide configuration values."""

MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024
MAX_ROWS = 50_000
MAX_COLUMNS = 100

GROQ_MODEL = "openai/gpt-oss-20b"
MAX_AGENT_TURNS = 8
MAX_AGENT_TOOL_CALLS = 8
MAX_GROQ_RETRIES = 2

"""Small, application-wide configuration values."""

MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024
MAX_ROWS = 50_000
MAX_COLUMNS = 100

GROQ_MODEL = "openai/gpt-oss-20b"
# Groq's local tool-calling guidance recommends lowering temperature when a
# model-generated tool call is rejected. Keep this separate from transport
# retry settings; it is used only for the one recovery request.
GROQ_TEMPERATURE = 0.5
GROQ_TOOL_CALL_RECOVERY_TEMPERATURE = 0.2
MAX_AGENT_TURNS = 8
MAX_AGENT_TOOL_CALLS = 8
MAX_GROQ_RETRIES = 2

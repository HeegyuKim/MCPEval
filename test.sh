uv run mcp-eval generate-tasks \
  --server mcp_servers/book/server.py \
  --model gpt-4.1-mini \
  --num-tasks 10 \
  --output data/book/evaluation_tasks.jsonl

mcp-eval verify-tasks \
  --server mcp_servers/book/server.py \
  --tasks-file data/book/evaluation_tasks.jsonl \
  --output data/book/evaluation_tasks_verified.jsonl


uv run mcp-eval generate-tasks \
  --server @openbnb/mcp-server-airbnb \
  --model gpt-4.1-mini \
  --num-tasks 10 \
  --output data/book/evaluation_tasks.jsonl


uv run mcp-eval generate-tasks \
  --server mcp_servers/tau2_airline/server.py \
  --model gpt-4.1-mini \
  --num-tasks 10 \
  --output data/tau2_airline/evaluation_tasks.jsonl

uv run mcp-eval verify-tasks \
  --server mcp_servers/tau2_airline/server.py \
  --tasks-file data/tau2_airline/evaluation_tasks.jsonl \
  --output data/tau2_airline/evaluation_tasks_verified.jsonl
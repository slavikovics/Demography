"""События потока ответа (SSE). Формат: `event: <name>\ndata: <json>\n\n`."""
import json
from typing import Any


def sse(event: str, data: Any) -> str:
    return f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'


# Имена событий (контракт с фронтендом):
#   run_start{model, request_id}      начало ответа
#   reasoning_delta{text}             фрагмент рассуждений модели
#   token{text}                       фрагмент текста ответа (markdown)
#   tool_call{id, name, arguments}    модель вызывает инструмент
#   tool_result{id, ok, duration_ms, counts, preview, truncated}
#   done{model, usage, iterations, duration_ms}
#   error{code, message}

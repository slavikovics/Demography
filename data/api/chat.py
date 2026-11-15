"""Эндпоинты чата: POST /chat/stream (SSE) и GET /chat/health."""
import asyncio
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Deque, Dict, List, Literal

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent.agent import is_configured, make_client, run_agent, _settings
from agent.events import sse
from agent.mcp_client import McpToolbox

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

MAX_MESSAGE_CHARS = 2000
RATE_LIMIT_REQUESTS = int(os.getenv('CHAT_RATE_LIMIT', '20'))     # запросов в минуту с одного адреса
RATE_LIMIT_WINDOW_SECONDS = 60
KEEPALIVE_SECONDS = 15

router = APIRouter(prefix='/chat', tags=['chat'])
_requests: Dict[str, Deque[float]] = defaultdict(deque)


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(min_length=1, max_length=60)
    language: Literal['russian', 'english'] = 'russian'


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Подключение к MCP-серверу на старте API (при недоступности — повторные попытки при первом запросе)."""
    toolbox = McpToolbox(os.getenv('MCP_URL', 'http://127.0.0.1:8000/mcp'), os.getenv('MCP_AUTH_TOKEN') or None)
    app.state.toolbox = toolbox
    app.state.llm = make_client()
    await toolbox.start()
    try:
        yield
    finally:
        await toolbox.stop()
        await app.state.llm.close()


def _check_rate_limit(client_id: str) -> None:
    now = time.monotonic()
    window = _requests[client_id]
    while window and now - window[0] > RATE_LIMIT_WINDOW_SECONDS:
        window.popleft()
    if len(window) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail='Слишком много запросов. Повторите через минуту.')
    window.append(now)


@router.get('/health')
async def chat_health(request: Request) -> dict:
    toolbox: McpToolbox = request.app.state.toolbox
    info = {'configured': is_configured(), 'model': _settings()['model'], 'mcp': {'connected': False, 'tools': []}}
    try:
        info['mcp'] = {'connected': True, 'tools': await toolbox.tool_names()}
    except ConnectionError as e:
        info['mcp']['error'] = str(e)
    return info


@router.post('/stream')
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    if not is_configured():
        raise HTTPException(status_code=503, detail='Чат не настроен: задайте OPENROUTER_API_KEY в data/.env.')
    if body.messages[-1].role != 'user':
        raise HTTPException(status_code=422, detail='Последнее сообщение должно быть от пользователя.')
    if len(body.messages[-1].content) > MAX_MESSAGE_CHARS:
        raise HTTPException(status_code=422, detail=f'Сообщение длиннее {MAX_MESSAGE_CHARS} символов.')
    if not body.messages[-1].content.strip():
        raise HTTPException(status_code=422, detail='Пустое сообщение.')

    _check_rate_limit(request.client.host if request.client else 'unknown')
    toolbox: McpToolbox = request.app.state.toolbox
    llm = request.app.state.llm
    messages = [m.model_dump() for m in body.messages]

    async def stream() -> AsyncIterator[str]:
        events = run_agent(messages, body.language, toolbox, llm)
        try:
            pending = asyncio.ensure_future(events.__anext__())
            while True:
                # «keep-alive»-комментарий не даёт прокси оборвать соединение во время долгих вызовов
                done, _ = await asyncio.wait({pending}, timeout=KEEPALIVE_SECONDS)
                if not done:
                    yield ': keep-alive\n\n'
                    continue
                try:
                    event = pending.result()
                except StopAsyncIteration:
                    break
                yield sse(event['event'], event['data'])
                pending = asyncio.ensure_future(events.__anext__())
        finally:
            if 'pending' in locals() and not pending.done():
                pending.cancel()
            await events.aclose()

    headers = {'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'}
    return StreamingResponse(stream(), media_type='text/event-stream', headers=headers)

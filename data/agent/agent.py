"""Агентный цикл: LLM (OpenRouter, стриминг) <-> инструменты MCP. Реализован как асинхронный генератор событий."""
import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from openai import AsyncOpenAI

from agent.mcp_client import McpToolbox
from agent.prompts import system_prompt

log = logging.getLogger('agent')

MAX_ITERATIONS = int(os.getenv('AGENT_MAX_ITERATIONS', '8'))
MAX_HISTORY_MESSAGES = 20
MAX_TOOL_RESULT_CHARS = 14000   # сколько символов результата инструмента получает модель
PREVIEW_CHARS = 4000            # сколько символов результата уходит в интерфейс
TOOL_TIMEOUT_SECONDS = 25.0
REQUEST_TIMEOUT_SECONDS = 150.0
MAX_OUTPUT_TOKENS = 4000


def _settings() -> dict:
    return {
        'api_key': os.getenv('OPENROUTER_API_KEY', ''),
        'model': os.getenv('OPENROUTER_MODEL', '~deepseek/deepseek-v4-flash-latest'),
        'effort': os.getenv('OPENROUTER_REASONING_EFFORT', 'low'),   # low | medium | high | none
    }


def is_configured() -> bool:
    return bool(_settings()['api_key'])


def make_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=_settings()['api_key'] or 'missing',
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=1,
        default_headers={'X-Title': 'Belarus Demography', 'HTTP-Referer': 'http://localhost:3001'},
    )


def _counts(text: str) -> Dict[str, int]:
    """Краткая сводка результата для интерфейса: сколько элементов в списках верхнего уровня."""
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    counts = {key: len(value) for key, value in data.items() if isinstance(value, list)}
    if isinstance(data.get('row_count'), int):
        counts['row_count'] = data['row_count']
    return counts


def _limit_for_model(text: str) -> str:
    if len(text) <= MAX_TOOL_RESULT_CHARS:
        return text
    return text[:MAX_TOOL_RESULT_CHARS] + '\n…[результат обрезан; уточните запрос: меньше территорий, лет или top_n]'


def _trim_history(messages: List[dict]) -> List[dict]:
    history = [{'role': m['role'], 'content': m['content']} for m in messages if m.get('content')]
    history = history[-MAX_HISTORY_MESSAGES:]
    while history and history[0]['role'] != 'user':
        history.pop(0)
    return history


async def run_agent(messages: List[dict], language: str, toolbox: McpToolbox,
                    client: Optional[AsyncOpenAI] = None) -> AsyncIterator[dict]:
    """Асинхронный генератор событий: dict {'event': <имя>, 'data': {...}} (см. agent/events.py)."""
    cfg = _settings()
    client = client or make_client()
    request_id = uuid.uuid4().hex[:12]
    started = time.monotonic()
    usage_total: Dict[str, Any] = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    cost = 0.0
    resolved_model = cfg['model']

    try:
        tools = await toolbox.openai_tools()
    except ConnectionError as e:
        yield {'event': 'error', 'data': {'code': 'mcp_unavailable', 'message': str(e)}}
        return

    conversation: List[dict] = [{'role': 'system', 'content': system_prompt(language)}] + _trim_history(messages)
    yield {'event': 'run_start', 'data': {'model': cfg['model'], 'request_id': request_id}}

    extra_body: Dict[str, Any] = {'provider': {'require_parameters': True}}
    if cfg['effort'] == 'none':
        extra_body['reasoning'] = {'enabled': False}
    else:
        extra_body['reasoning'] = {'effort': cfg['effort']}

    for iteration in range(1, MAX_ITERATIONS + 1):
        last_round = iteration == MAX_ITERATIONS
        content, reasoning_details = '', []
        calls: Dict[int, dict] = {}

        try:
            stream = await client.chat.completions.create(
                model=cfg['model'], messages=conversation, tools=tools,
                tool_choice='none' if last_round else 'auto',   # на последнем круге — только ответ
                stream=True, stream_options={'include_usage': True},
                max_tokens=MAX_OUTPUT_TOKENS, temperature=0.2, extra_body=extra_body)

            async for chunk in stream:
                resolved_model = chunk.model or resolved_model
                if getattr(chunk, 'usage', None):
                    usage = chunk.usage
                    for key in usage_total:
                        usage_total[key] += getattr(usage, key, 0) or 0
                    cost += float((getattr(usage, 'model_extra', None) or {}).get('cost') or 0)
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                extra = getattr(delta, 'model_extra', None) or {}
                if extra.get('reasoning'):
                    yield {'event': 'reasoning_delta', 'data': {'text': extra['reasoning']}}
                if extra.get('reasoning_details'):
                    reasoning_details.extend(extra['reasoning_details'])
                if delta.content:
                    content += delta.content
                    yield {'event': 'token', 'data': {'text': delta.content}}
                for call in delta.tool_calls or []:
                    slot = calls.setdefault(call.index, {'id': '', 'name': '', 'arguments': ''})
                    slot['id'] = call.id or slot['id']
                    if call.function:
                        slot['name'] = call.function.name or slot['name']
                        slot['arguments'] += call.function.arguments or ''
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            log.exception('LLM request failed')
            yield {'event': 'error', 'data': {'code': 'llm_error', 'message': _friendly_llm_error(e)}}
            return

        ordered = [calls[i] for i in sorted(calls) if calls[i]['name']]
        if not ordered:
            yield {'event': 'done', 'data': {
                'model': resolved_model, 'usage': usage_total, 'cost': round(cost, 6) or None, 'iterations': iteration,
                'duration_ms': int((time.monotonic() - started) * 1000), 'request_id': request_id}}
            return

        # у некоторых провайдеров id может не прийти — генерируем, чтобы связать вызов и результат
        for call in ordered:
            call['id'] = call['id'] or f'call_{uuid.uuid4().hex[:10]}'

        assistant: Dict[str, Any] = {'role': 'assistant', 'content': content or None, 'tool_calls': [
            {'id': c['id'], 'type': 'function', 'function': {'name': c['name'], 'arguments': c['arguments'] or '{}'}}
            for c in ordered]}
        if reasoning_details:
            assistant['reasoning_details'] = reasoning_details
        conversation.append(assistant)

        parsed: Dict[str, dict] = {}
        for call in ordered:
            try:
                parsed[call['id']] = json.loads(call['arguments'] or '{}')
            except ValueError:
                parsed[call['id']] = {}
            yield {'event': 'tool_call', 'data': {'id': call['id'], 'name': call['name'], 'arguments': parsed[call['id']]}}

        async def execute(call: dict):
            began = time.monotonic()
            try:
                ok, text = await toolbox.call(call['name'], parsed[call['id']], timeout=TOOL_TIMEOUT_SECONDS)
            except ConnectionError as e:   # MCP-сервер пропал посреди ответа — продолжать бессмысленно
                ok, text = False, str(e)
                fatal.append(text)
            return call, ok, text, int((time.monotonic() - began) * 1000)

        results: Dict[str, str] = {}
        fatal: List[str] = []
        pending = [asyncio.create_task(execute(c)) for c in ordered]
        try:
            for finished in asyncio.as_completed(pending):
                call, ok, text, duration = await finished
                results[call['id']] = _limit_for_model(text)
                yield {'event': 'tool_result', 'data': {
                    'id': call['id'], 'name': call['name'], 'ok': ok, 'duration_ms': duration, 'counts': _counts(text),
                    'preview': text[:PREVIEW_CHARS], 'truncated': len(text) > PREVIEW_CHARS}}
        finally:
            for task in pending:
                if not task.done():
                    task.cancel()

        if fatal:
            yield {'event': 'error', 'data': {'code': 'mcp_unavailable', 'message': fatal[0]}}
            return

        for call in ordered:   # порядок сообщений tool — как порядок вызовов
            conversation.append({'role': 'tool', 'tool_call_id': call['id'], 'content': results.get(call['id'], '')})

    yield {'event': 'error', 'data': {'code': 'max_iterations', 'message': 'Слишком много шагов. Попробуйте задать вопрос точнее.'}}


def _friendly_llm_error(error: Exception) -> str:
    text = str(error)
    status = getattr(error, 'status_code', None)
    if status == 401:
        return 'Ключ OpenRouter отклонён (401). Проверьте OPENROUTER_API_KEY.'
    if status == 402:
        return 'На счёте OpenRouter недостаточно средств (402).'
    if status == 429:
        return 'Превышен лимит запросов к модели (429). Повторите через минуту.'
    return f'Ошибка модели: {text[:300]}'

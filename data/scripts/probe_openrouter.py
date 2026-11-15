"""Проверка возможностей модели на OpenRouter для агента (запускать вручную).

    python -m scripts.probe_openrouter

Проверяет: стриминг, стриминг tool-calls, полный цикл tool_calls -> результат -> ответ,
возврат reasoning между итерациями, русский язык. Ключ нигде не печатается.
"""
import json
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv('OPENROUTER_MODEL', '~deepseek/deepseek-v4-flash-latest')
client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=os.environ['OPENROUTER_API_KEY'],
                default_headers={'X-Title': 'Belarus Demography probe'})

TOOLS = [{
    'type': 'function',
    'function': {
        'name': 'get_births',
        'description': 'Возвращает число родившихся в районе за год.',
        'parameters': {
            'type': 'object',
            'properties': {'district': {'type': 'string'}, 'year': {'type': 'integer'}},
            'required': ['district', 'year'],
        },
    },
}]

# provider.require_parameters: маршрутизация только на провайдеров, поддерживающих все параметры запроса
EXTRA = {'provider': {'require_parameters': True}}


def stream_once(messages, reasoning=None, tools=None):
    """Один запрос со стримингом. Возвращает (content, reasoning_text, tool_calls, reasoning_details, model, usage)."""
    extra = dict(EXTRA)
    if reasoning is not None:
        extra['reasoning'] = reasoning
    kwargs = dict(model=MODEL, messages=messages, stream=True, extra_body=extra,
                  stream_options={'include_usage': True}, max_tokens=800)
    if tools:
        kwargs.update(tools=tools, tool_choice='auto')

    content, reasoning_text, calls, details, model, usage = '', '', {}, [], None, None
    chunks = 0
    for chunk in client.chat.completions.create(**kwargs):
        chunks += 1
        model = chunk.model or model
        if getattr(chunk, 'usage', None):
            usage = chunk.usage
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        content += delta.content or ''
        extra_fields = getattr(delta, 'model_extra', None) or {}
        reasoning_text += extra_fields.get('reasoning') or ''
        if extra_fields.get('reasoning_details'):
            details.extend(extra_fields['reasoning_details'])
        for call in delta.tool_calls or []:
            slot = calls.setdefault(call.index, {'id': '', 'name': '', 'arguments': ''})
            slot['id'] = call.id or slot['id']
            if call.function:
                slot['name'] = call.function.name or slot['name']
                slot['arguments'] += call.function.arguments or ''
    return content, reasoning_text, [calls[i] for i in sorted(calls)], details, model, usage, chunks


def check(title, fn):
    started = time.time()
    try:
        result = fn()
        print(f'[OK ] {title} ({time.time() - started:.1f}s)')
        return result
    except Exception as e:  # noqa: BLE001
        print(f'[ERR] {title}: {type(e).__name__}: {str(e)[:300]}')
        return None


def main():
    print(f'Модель: {MODEL}')

    r = check('1. обычный стриминг (RU)', lambda: stream_once(
        [{'role': 'user', 'content': 'Ответь одним коротким предложением: столица Беларуси?'}]))
    if r:
        print(f'     ответ: {r[0][:120]!r} | чанков: {r[6]} | реальная модель: {r[4]} | reasoning: {len(r[1])} симв.')

    r = check('2. стриминг tool-call (аргументы по дельтам)', lambda: stream_once(
        [{'role': 'user', 'content': 'Сколько родилось в Барановичском районе в 2023 году? Используй инструмент.'}],
        tools=TOOLS))
    if not r or not r[2]:
        print('     tool_calls не получены — дальнейшие проверки цикла невозможны')
        return
    content, reasoning_text, calls, details, model, usage, chunks = r
    print(f'     вызовы: {[(c["name"], c["arguments"]) for c in calls]} | reasoning: {len(reasoning_text)} симв., details: {len(details)}')

    base = [{'role': 'user', 'content': 'Сколько родилось в Барановичском районе в 2023 году? Используй инструмент.'}]
    assistant = {'role': 'assistant', 'content': content or None, 'tool_calls': [
        {'id': c['id'], 'type': 'function', 'function': {'name': c['name'], 'arguments': c['arguments']}} for c in calls]}
    tool_msgs = [{'role': 'tool', 'tool_call_id': c['id'], 'content': json.dumps({'births': 1334, 'year': 2023})} for c in calls]

    for label, with_reasoning in (('3a. цикл БЕЗ возврата reasoning', False), ('3b. цикл С возвратом reasoning', True)):
        msg = dict(assistant)
        if with_reasoning and details:
            msg['reasoning_details'] = details
        elif with_reasoning and reasoning_text:
            msg['reasoning'] = reasoning_text
        res = check(label, lambda m=msg: stream_once(base + [m] + tool_msgs, tools=TOOLS))
        if res:
            print(f'     ответ: {res[0][:160]!r}')

    r = check('4. reasoning выключен (reasoning.enabled=false)', lambda: stream_once(
        base, reasoning={'enabled': False}, tools=TOOLS))
    if r:
        print(f'     вызовы: {[(c["name"], c["arguments"]) for c in r[2]]} | reasoning: {len(r[1])} симв.')


if __name__ == '__main__':
    sys.exit(main())

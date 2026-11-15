"""Прогон эталонных вопросов через /chat/stream с проверкой «каждое число ответа есть в результатах инструментов».

    python -m scripts.eval_agent [--base http://127.0.0.1:5000]

Числа, которых нет в результатах инструментов (например, разность или доля, посчитанные самой моделью), выводятся
как «непроверенные» для ручного просмотра; годы и номера мест (1–10) не проверяются.
"""
import argparse
import json
import re
import time

import httpx

CASES = [
    # (вопрос, язык, ожидаемые инструменты (любой из), числа, которые обязаны встретиться в ответе)
    ('Сколько родилось в Минске в 2024 и в 2019 году?', 'russian', {'get_series', 'territory_profile', 'search_territories'}, ['10 143', '15 881']),
    ('Назови 5 районов с наибольшим числом браков на 1000 человек в 2024 году.', 'russian', {'rank_territories'}, []),
    ('Как менялась численность населения Гомельской области с 2010 по 2024 год?', 'russian', {'get_series', 'region_totals'}, ['1 333 295']),
    ('Каков прогноз численности населения Беларуси на 2030 год по разным моделям?', 'russian', {'get_series', 'rank_territories', 'region_totals', 'territory_profile'}, []),
    ('Сколько родилось в Барановичах в 2021 году?', 'russian', {'search_territories', 'get_series', 'list_indicators', 'territory_profile'}, []),
    ('Сравни миграционный прирост по областям в 2024 году.', 'russian', {'region_totals'}, []),
    ('Где в 2024 году самая большая естественная убыль населения? Топ-3 района.', 'russian', {'rank_territories'}, []),
    ('Какая столица у Франции?', 'russian', set(), []),
    ('Покажи основные показатели Витебского района за 2024 год.', 'russian', {'territory_profile', 'search_territories'}, []),
    ('Какова плотность населения в Минске?', 'russian', {'territory_profile', 'get_series', 'rank_territories', 'search_territories'}, ['5 635,3']),
    ('What was the population of Gomel region in 2024?', 'english', {'region_totals', 'get_series'}, ['1,333,295']),
    ('На сколько изменилось число браков в Беларуси с 2010 по 2024 год?', 'russian', {'compare_years', 'get_series'}, ['76 978', '46 242']),
]

NUMBER = re.compile(r'(?<![\w.])\d{1,3}(?:[\s ,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?')


def parse_numbers(text):
    values = set()
    for raw in NUMBER.findall(text):
        cleaned = raw.replace(' ', ' ')
        if re.fullmatch(r'\d{1,3}(?: \d{3})+(?:[.,]\d+)?', cleaned):
            cleaned = cleaned.replace(' ', '')
        elif re.fullmatch(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?', cleaned):
            cleaned = cleaned.replace(',', '')
        cleaned = cleaned.replace(',', '.')
        try:
            values.add(round(float(cleaned), 3))
        except ValueError:
            pass
    return values


def ask(base, question, language):
    body = {'messages': [{'role': 'user', 'content': question}], 'language': language}
    answer, calls, results, done, error = '', [], [], None, None
    with httpx.stream('POST', f'{base}/chat/stream', json=body, timeout=170) as r:
        if r.status_code != 200:
            return {'error': f'HTTP {r.status_code} {r.read().decode()[:200]}'}
        event = None
        for line in r.iter_lines():
            if line.startswith('event: '):
                event = line[7:]
            elif line.startswith('data: '):
                data = json.loads(line[6:])
                if event == 'token':
                    answer += data['text']
                elif event == 'tool_call':
                    calls.append(data)
                elif event == 'tool_result':
                    results.append(data)
                elif event == 'done':
                    done = data
                elif event == 'error':
                    error = data
    return {'answer': answer, 'calls': calls, 'results': results, 'done': done, 'error': error}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:5000')
    args = parser.parse_args()
    failed = 0

    for question, language, expected_tools, must_have in CASES:
        started = time.time()
        out = ask(args.base, question, language)
        print(f'\n=== {question}')
        if out.get('error') and not out.get('answer'):
            print('  FAIL:', out['error'])
            failed += 1
            continue
        tools_used = [c['name'] for c in out['calls']]
        problems = []
        if expected_tools and not (set(tools_used) & expected_tools):
            problems.append(f'ожидался один из инструментов {sorted(expected_tools)}, вызваны {tools_used}')
        if not expected_tools and tools_used:
            problems.append(f'инструменты не нужны, но вызваны: {tools_used}')
        if any(not r['ok'] for r in out['results']):
            print('  (были ошибки инструментов:', [r['preview'][:80] for r in out['results'] if not r['ok']], ')')

        tool_numbers = set()
        for result in out['results']:
            tool_numbers |= parse_numbers(result['preview'])
        answer_numbers = parse_numbers(out['answer'])
        unverified = sorted(n for n in answer_numbers
                            if n not in tool_numbers and not (1900 <= n <= 2100) and n > 10)
        for needle in must_have:
            if not (parse_numbers(needle) & answer_numbers):
                problems.append(f'в ответе нет ожидаемого числа {needle}')

        usage = out['done']['usage']['total_tokens'] if out.get('done') else None
        print(f'  инструменты: {tools_used} | {time.time() - started:.1f}s | токенов: {usage} | модель: {out.get("done", {}).get("model")}')
        print('  ответ:', out['answer'].strip().replace('\n', ' ')[:420])
        if unverified:
            print('  непроверенные числа (нет в результатах инструментов):', unverified[:12])
        if problems:
            failed += 1
            for p in problems:
                print('  FAIL:', p)
        else:
            print('  OK')

    print(f'\nИтого: {len(CASES) - failed}/{len(CASES)} без замечаний')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())

"""MCP-сервер «demography»: инструменты доступа к демографической статистике Беларуси.

Запуск:  python -m mcp_server           (streamable HTTP, http://127.0.0.1:8000/mcp)
Подключение, например, к Claude Code:  claude mcp add --transport http demography http://127.0.0.1:8000/mcp
"""
from typing import Annotated, List, Literal, Optional

import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server import tools

INSTRUCTIONS = """\
Демографическая статистика Республики Беларусь по районам (источник — Белстат) и прогнозы на 2025–2034 годы.
Рабочий порядок: 1) list_indicators — какие показатели и годы есть; 2) search_territories — найти id территории;
3) get_series / rank_territories / compare_years / region_totals / territory_profile — получить числа.
Все значения возвращаются как есть из базы; прогнозы помечены source = forecast:<модель>."""

# Разрешаем обращение по имени сервиса из сети compose (иначе «Invalid Host header: mcp:8000»).
_allowed_hosts = [h.strip() for h in os.getenv('MCP_ALLOWED_HOSTS', 'mcp:*,localhost:*,127.0.0.1:*').split(',') if h.strip()]
mcp = FastMCP(
    'demography', instructions=INSTRUCTIONS, log_level='WARNING',
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True, allowed_hosts=_allowed_hosts, allowed_origins=['*']),
)

IndicatorArg = Annotated[str, Field(description=(
    "Показатель: код (например '10101200001'), ключ ('births', 'deaths', 'net_migration', 'marriages', "
    "'population_density', 'births_per_1000' …), или 'population' для численности населения. "
    "Полный список — list_indicators()."))]
ModelArg = Annotated[Literal['historical', 'prophet', 'linear', 'exponential'], Field(description=(
    "'historical' — опубликованные данные Белстата. 'prophet' / 'linear' / 'exponential' — прогноз соответствующей модели "
    "(нужен для лет после последнего опубликованного). Для прошлых лет всегда возвращаются факты."))]
GenderArg = Annotated[Literal['total', 'male', 'female'], Field(description="Пол; только для показателя population.")]


@mcp.tool()
def list_indicators() -> dict:
    """Каталог показателей: код, название, единица, тема, доступные годы (с пропусками), годы прогноза по моделям
    и важные замечания о данных. Вызывайте первым, если не уверены, какой показатель или год доступен."""
    return tools.list_indicators()


@mcp.tool()
def search_territories(
    query: Annotated[str, Field(description="Название района, города или области в любом падеже: 'Барановичи', 'в Гомельской области', 'Minsk'.")],
    limit: Annotated[int, Field(ge=1, le=25, description='Сколько результатов вернуть.')] = 10,
) -> dict:
    """Находит территории по названию и возвращает их id и уровень (республика / область / район / город / г. Минск).
    id нужен остальным инструментам. Район «Брестский» включает г. Брест — об этом сказано в поле includes_city."""
    return tools.search_territories(query, limit)


@mcp.tool()
def get_series(
    indicator: IndicatorArg,
    territory_ids: Annotated[List[int], Field(min_length=1, max_length=10, description='id территорий (до 10). Республика — 699961, г. Минск — 919071; области тоже поддерживаются (сумма по районам).')],
    year_from: Annotated[Optional[int], Field(description='Первый год (по умолчанию 2010).')] = None,
    year_to: Annotated[Optional[int], Field(description='Последний год (по умолчанию 2034).')] = None,
    models: Annotated[Optional[List[ModelArg]], Field(description="Какие ряды вернуть. По умолчанию ['historical']. Чтобы получить факты и прогноз, укажите ['historical', 'prophet'].")] = None,
    gender: GenderArg = 'total',
) -> dict:
    """Динамика показателя по годам для одной или нескольких территорий. Ответ: для каждой территории и модели —
    словарь {год: значение}. Пропущенные годы (например, 2020–2023 для рождений по районам) в ряде отсутствуют."""
    return tools.get_series(indicator, territory_ids, year_from, year_to, models, gender)


@mcp.tool()
def rank_territories(
    indicator: IndicatorArg,
    year: Annotated[int, Field(description='Год (2010–2034).')],
    model: ModelArg = 'historical',
    top_n: Annotated[int, Field(ge=1, le=50)] = 10,
    order: Annotated[Literal['desc', 'asc'], Field(description="'desc' — от большего к меньшему.")] = 'desc',
    oblast: Annotated[Optional[str], Field(description="Ограничить областью: название ('Гомельская') или id. Пусто — вся страна.")] = None,
    scope: Annotated[Literal['districts', 'cities', 'all'], Field(description="districts — районы (по умолчанию, значения включают города областного подчинения); cities — города областного подчинения и Минск; all — всё вместе.")] = 'districts',
    gender: GenderArg = 'total',
) -> dict:
    """Рейтинг территорий по показателю за год: топ-N с местом в рейтинге, а также среднее, медиана, минимум, максимум
    и значение по республике для контекста. Для вопросов «где больше/меньше всего …»."""
    return tools.rank_territories(indicator, year, model, top_n, order, oblast, scope, gender)


@mcp.tool()
def compare_years(
    indicator: IndicatorArg,
    year_from: Annotated[int, Field(description='Начальный год.')],
    year_to: Annotated[int, Field(description='Конечный год.')],
    model: ModelArg = 'historical',
    top_n: Annotated[int, Field(ge=1, le=50)] = 10,
    territory_ids: Annotated[Optional[List[int]], Field(max_length=25, description='Сравнить только эти территории (иначе — лидеры роста и падения среди районов).')] = None,
    scope: Annotated[Literal['districts', 'cities', 'all'], Field()] = 'districts',
    gender: GenderArg = 'total',
) -> dict:
    """Изменение показателя между двумя годами: абсолютное и в процентах, лидеры роста и падения (или выбранные
    территории) и значение по республике. Для вопросов «как изменилось», «где выросло/упало сильнее всего»."""
    return tools.compare_years(indicator, year_from, year_to, model, top_n, territory_ids, scope, gender)


@mcp.tool()
def region_totals(
    indicator: IndicatorArg,
    year: Annotated[int, Field(description='Год (2010–2034).')],
    model: ModelArg = 'historical',
    gender: GenderArg = 'total',
) -> dict:
    """Итоги по шести областям, г. Минску и республике за год. Области считаются суммой районов (города областного
    подчинения не добавляются повторно); коэффициенты на 1000 пересчитываются. Плотность населения не поддерживается."""
    return tools.region_totals(indicator, year, model, gender)


@mcp.tool()
def territory_profile(
    territory_id: Annotated[int, Field(description='id территории из search_territories (республика 699961, область, район, город).')],
    year: Annotated[int, Field(description='Год (2010–2034).')],
    model: ModelArg = 'historical',
) -> dict:
    """Все показатели одной территории за год сразу: население (всего, мужчины, женщины), плотность, рождения, смерти,
    естественный прирост, браки, разводы, миграция, а также значение по республике для сравнения."""
    return tools.territory_profile(territory_id, year, model)


@mcp.tool(description=(
    "Запасной инструмент: один read-only SQL-запрос (SELECT / WITH) к базе, если остальные инструменты не подходят "
    "(нестандартные агрегаты, фильтры, соединения). Лимит строк и времени. Предпочитайте специализированные инструменты.\n\n"
    + tools.SQL_SCHEMA))
def run_sql(
    query: Annotated[str, Field(description='Один SELECT-запрос без точки с запятой.')],
    max_rows: Annotated[int, Field(ge=1, le=200)] = 100,
) -> dict:
    return tools.run_sql(query, max_rows)


@mcp.custom_route('/health', methods=['GET'])
async def health(_: Request) -> JSONResponse:
    try:
        info = tools.list_indicators()
        return JSONResponse({'status': 'ok', 'indicators': len(info['indicators'])})
    except Exception as e:  # noqa: BLE001
        return JSONResponse({'status': 'error', 'detail': str(e)}, status_code=503)

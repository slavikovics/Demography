"""Тесты инструментов MCP-сервера на реальной demography.db (пропускаются, если базы нет).

    pytest data/tests -q
"""
import pytest

from mcp_server import store, tools
from mcp_server.store import ToolInputError

pytestmark = pytest.mark.skipif(not __import__('os').path.exists(store.db_path()), reason='demography.db не найдена')

BELARUS, MINSK, BARANOVICHY_DISTRICT, GOMEL_OBLAST = 699961, 919071, 919075, 919069


def points(result, index=0):
    return result['series'][index]['points']


def test_reference_numbers_republic_and_minsk():
    births = tools.get_series('births', [BELARUS, MINSK], 2024, 2024)
    assert points(births, 0)['2024'] == 58938
    assert points(births, 1)['2024'] == 10143
    deaths = tools.get_series('deaths', [BELARUS], 2024, 2024)
    assert points(deaths)['2024'] == 115124


def test_migration_balance_equals_arrivals_minus_departures():
    arrivals = points(tools.get_series('immigrants', [MINSK], 2024, 2024))['2024']
    departures = points(tools.get_series('emigrants', [MINSK], 2024, 2024))['2024']
    balance = points(tools.get_series('net_migration', [MINSK], 2024, 2024))['2024']
    assert balance == arrivals - departures == 11921


def test_region_totals_sum_equals_republic():
    for indicator in ('births', 'deaths', 'population', 'marriages'):
        result = tools.region_totals(indicator, 2024)
        assert result['sum_of_regions'] == result['republic'], indicator
        assert len(result['regions']) == 7  # 6 областей + Минск


def test_district_includes_regional_city():
    district = points(tools.get_series('births', [BARANOVICHY_DISTRICT], 2024, 2024))['2024']
    city = points(tools.get_series('births', [919093], 2024, 2024))['2024']
    assert district == 1334 and city == 1136 and district > city


def test_oblast_series_is_sum_of_districts():
    series = points(tools.get_series('births', [GOMEL_OBLAST], 2019, 2019))
    assert series['2019'] == 13710


def test_gap_years_are_reported_not_invented():
    with pytest.raises(ToolInputError, match='2010–2019, 2024–2025'):
        tools.rank_territories('births', 2021)
    series = tools.get_series('births', [MINSK], 2018, 2025)
    assert set(points(series)) == {'2018', '2019', '2024', '2025'}


def test_future_requires_model_and_is_marked_forecast():
    with pytest.raises(ToolInputError, match='prophet'):
        tools.rank_territories('population', 2030)
    ranked = tools.rank_territories('population', 2030, 'prophet', top_n=3)
    assert ranked['source'] == 'forecast:prophet' and len(ranked['rows']) == 3


def test_past_year_with_forecast_model_uses_facts():
    ranked = tools.rank_territories('births', 2024, 'prophet', top_n=2)
    assert ranked['source'] == 'belstat' and any('опубликованные данные' in n for n in ranked['notes'])


def test_rank_is_sorted_and_scoped():
    ranked = tools.rank_territories('births_per_1000', 2024, top_n=5)
    values = [r['value'] for r in ranked['rows']]
    assert values == sorted(values, reverse=True)
    assert all(r['id'] not in (BELARUS, MINSK) for r in ranked['rows'])
    gomel = tools.rank_territories('births_per_1000', 2024, top_n=50, oblast='Гомельская')
    assert {r['oblast'] for r in gomel['rows']} == {'Гомельская область'}


def test_search_handles_cases_and_english():
    assert tools.search_territories('Барановичах')['results'][0]['id'] in (919093, BARANOVICHY_DISTRICT)
    assert tools.search_territories('gomel')['results'][0]['name_ru'].startswith('Гомел')
    assert tools.search_territories('в Минске')['results'][0]['id'] == MINSK


@pytest.mark.parametrize('bad', [
    'DROP TABLE population', 'SELECT 1; SELECT 2', 'PRAGMA table_info(population)',
    "ATTACH DATABASE 'x.db' AS x", 'SELECT * FROM sqlite_master', "SELECT load_extension('x')",
    'WITH x AS (SELECT 1) INSERT INTO population VALUES (1)',
])
def test_run_sql_rejects_everything_but_select(bad):
    with pytest.raises(ToolInputError):
        tools.run_sql(bad)


def test_run_sql_select_limits_and_timeout():
    ok = tools.run_sql("SELECT territory_id, value FROM indicators WHERE model='historical'", max_rows=5)
    assert ok['row_count'] == 5 and ok['truncated'] is True
    with pytest.raises(ToolInputError, match='долгий'):
        tools.run_sql('WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c WHERE x<2000000000) SELECT count(*) FROM c')


def test_database_is_read_only():
    conn = store.connect()
    try:
        with pytest.raises(Exception):
            conn.execute('DELETE FROM population')
    finally:
        conn.close()


def test_unknown_inputs_have_helpful_errors():
    with pytest.raises(ToolInputError, match='list_indicators'):
        tools.get_series('nonsense', [MINSK])
    with pytest.raises(ToolInputError, match='search_territories'):
        tools.get_series('births', [1])
    with pytest.raises(ToolInputError, match='не более|максимум'):
        tools.get_series('births', list(range(1, 12)))

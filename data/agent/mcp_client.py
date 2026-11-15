"""Постоянное подключение к MCP-серверу (streamable HTTP) с автопереподключением.

Соединение принадлежит отдельной фоновой задаче: контексты anyio должны открываться и закрываться
в одной и той же задаче, поэтому запросы обработчиков только пользуются готовой сессией.
"""
import asyncio
import copy
import logging
from typing import Any, Dict, List, Optional, Tuple

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

log = logging.getLogger('agent.mcp')


def _strip_titles(schema: Any) -> Any:
    """Убирает «title» из JSON-схемы: модели они не нужны, а токены стоят денег."""
    if isinstance(schema, dict):
        return {k: _strip_titles(v) for k, v in schema.items() if k != 'title'}
    if isinstance(schema, list):
        return [_strip_titles(v) for v in schema]
    return schema


class McpToolbox:
    def __init__(self, url: str, token: Optional[str] = None, connect_timeout: float = 15.0):
        self.url = url
        self.token = token
        self.connect_timeout = connect_timeout
        self._session: Optional[ClientSession] = None
        self._tools: List[dict] = []
        self._runner: Optional[asyncio.Task] = None
        self._ready = asyncio.Event()
        self._broken = asyncio.Event()
        self._stop = asyncio.Event()
        self._lock = asyncio.Lock()
        self.last_error: Optional[str] = None

    # ------------------------------------------------------------------ жизненный цикл

    async def _run(self) -> None:
        headers = {'Authorization': f'Bearer {self.token}'} if self.token else None
        try:
            async with streamablehttp_client(self.url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    self._tools = [{
                        'name': t.name,
                        'description': t.description or '',
                        'parameters': _strip_titles(copy.deepcopy(t.inputSchema)),
                    } for t in listed.tools]
                    self._session = session
                    self.last_error = None
                    self._ready.set()
                    waiters = [asyncio.create_task(self._broken.wait()), asyncio.create_task(self._stop.wait())]
                    await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)
                    for waiter in waiters:
                        waiter.cancel()
        except asyncio.CancelledError:
            raise
        except BaseException as e:  # noqa: BLE001  (в т.ч. ExceptionGroup из anyio)
            self.last_error = f'{type(e).__name__}: {e}'
            log.warning('MCP connection failed: %s', self.last_error)
        finally:
            self._session = None
            self._ready.clear()

    async def _alive(self) -> bool:
        """Быстрая проверка, что соединение живо: ping с коротким тайм-аутом."""
        if not self.connected:
            return False
        try:
            await asyncio.wait_for(self._session.send_ping(), timeout=3)
            return True
        except Exception:  # noqa: BLE001
            self.last_error = 'нет ответа на ping'
            self._broken.set()
            return False

    async def ensure(self, verify: bool = True) -> None:
        """Гарантирует живую сессию; при обрыве переподключается. Если сервер недоступен — ConnectionError."""
        async with self._lock:
            if self._runner and not self._runner.done() and self.connected and (not verify or await self._alive()):
                return
            await self._shutdown_runner()
            self._broken.clear()
            self._stop.clear()
            self._runner = asyncio.create_task(self._run(), name='mcp-connection')
            ready = asyncio.create_task(self._ready.wait())
            done, _ = await asyncio.wait({ready, self._runner}, timeout=self.connect_timeout,
                                         return_when=asyncio.FIRST_COMPLETED)
            if ready not in done:
                ready.cancel()
                await self._shutdown_runner()
                log.warning('MCP недоступен (%s): %s', self.url, self.last_error or 'таймаут подключения')
                raise ConnectionError('Сервер с инструментами (MCP) недоступен. Запустите его и повторите запрос.')

    async def _shutdown_runner(self) -> None:
        if self._runner and not self._runner.done():
            self._stop.set()
            try:
                await asyncio.wait_for(self._runner, timeout=5)
            except (asyncio.TimeoutError, asyncio.CancelledError, Exception):  # noqa: BLE001
                self._runner.cancel()
        self._runner = None

    async def start(self) -> None:
        try:
            await self.ensure()
        except ConnectionError as e:
            log.warning('%s — будет повторная попытка при первом запросе', e)

    async def stop(self) -> None:
        await self._shutdown_runner()

    # ------------------------------------------------------------------ использование

    @property
    def connected(self) -> bool:
        return self._session is not None and self._ready.is_set() and not self._broken.is_set()

    async def openai_tools(self) -> List[dict]:
        await self.ensure()
        return [{'type': 'function', 'function': t} for t in self._tools]

    async def tool_names(self) -> List[str]:
        await self.ensure()
        return [t['name'] for t in self._tools]

    async def call(self, name: str, arguments: Dict[str, Any], timeout: float = 25.0) -> Tuple[bool, str]:
        """Вызывает инструмент. Возвращает (ok, текст). Ошибки самого инструмента — не исключения: их читает модель.
        Если MCP-сервер недоступен — ConnectionError (ответ агента при этом невозможен)."""
        await self.ensure()
        try:
            result = await asyncio.wait_for(self._session.call_tool(name, arguments), timeout=timeout)
            text = '\n'.join(part.text for part in result.content if getattr(part, 'text', None))
            return (not result.isError), text
        except asyncio.TimeoutError:
            self._broken.set()   # следующий вызов переподключится
            return False, f'Инструмент {name} не ответил за {timeout:.0f} с.'
        except Exception as e:  # noqa: BLE001  (обрыв соединения, ошибки протокола MCP)
            self.last_error = f'{type(e).__name__}: {e}'
            log.warning('Вызов инструмента %s не удался: %s', name, self.last_error)
            self._broken.set()
            raise ConnectionError('Сервер с инструментами (MCP) недоступен. Запустите его и повторите запрос.') from e

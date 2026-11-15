"""Запуск MCP-сервера: python -m mcp_server [--host 127.0.0.1] [--port 8000]"""
import argparse
import hmac
import os

import uvicorn
from dotenv import load_dotenv
from starlette.responses import JSONResponse

from mcp_server.server import mcp


class BearerAuthMiddleware:
    """Необязательная защита общим секретом: Authorization: Bearer <MCP_AUTH_TOKEN>. /health открыт."""

    def __init__(self, app, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http' and scope['path'] != '/health':
            headers = dict(scope['headers'])
            given = headers.get(b'authorization', b'').decode()
            if not hmac.compare_digest(given, f'Bearer {self.token}'):
                response = JSONResponse({'error': 'unauthorized'}, status_code=401)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def build_app():
    app = mcp.streamable_http_app()
    token = os.getenv('MCP_AUTH_TOKEN')
    if token:
        app.add_middleware(BearerAuthMiddleware, token=token)
    return app


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description='MCP-сервер демографической статистики')
    parser.add_argument('--host', default=os.getenv('MCP_HOST', '127.0.0.1'))
    parser.add_argument('--port', type=int, default=int(os.getenv('MCP_PORT', '8000')))
    args = parser.parse_args()
    uvicorn.run(build_app(), host=args.host, port=args.port, log_level='warning')


if __name__ == '__main__':
    main()

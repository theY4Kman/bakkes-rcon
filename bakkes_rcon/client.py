import json
from typing import Any, Dict, List, Optional, TypeVar

import websockets.client

from bakkes_rcon.exceptions import AuthenticationError, NotConnectedError
from bakkes_rcon.inventory import InventoryItem
from bakkes_rcon.types import RawInventoryItem
from bakkes_rcon.util import quote_arg

__all__ = ['BakkesRconClient']

BakkesRconClient_t = TypeVar('BakkesRconClient_t', bound='BakkesRconClient')


class BakkesRconClient:
    host: str
    port: int
    password: Optional[str]

    ws_opts: Dict[str, Any]
    ws: Optional[websockets.client.WebSocketClientProtocol]

    def __init__(
        self,
        host: str = '127.0.0.1',
        port: int = 9002,
        password: Optional[str] = 'password',
        *,
        ws_opts: Dict[str, Any] = None
    ):
        self.host = host
        self.port = port
        self.password = password

        if ws_opts is None:
            ws_opts = {}
        self.ws_opts = {
            # Don't limit response size.
            # Some responses (like ws_inventory's) may be massive.
            'max_size': None,
            **ws_opts,
        }
        self.ws = None

    @property
    def ws_url(self):
        return f'ws://{self.host}:{self.port}'

    async def __aenter__(self: BakkesRconClient_t) -> 'BakkesRconClient':
        self.ws = await websockets.client.connect(self.ws_url, **self.ws_opts)

        if self.password is not None:
            await self.authenticate()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ws is not None:
            await self.ws.close()

    async def request(self, cmd: str, *args: str) -> str | bytes:
        if self.ws is None:
            raise NotConnectedError('Client must be connected first')

        cmdline = ' '.join((cmd, *map(quote_arg, args)))
        await self.ws.send(cmdline)
        return await self.ws.recv()

    async def authenticate(self):
        res = await self.request('rcon_password', self.password)
        if res != 'authyes':
            raise AuthenticationError(
                'Unable to authenticate with server — is the password correct?'
            )

    async def get_raw_inventory(self) -> List[RawInventoryItem]:
        raw_json = await self.request('ws_inventory', 'json', 'aaaa')
        res = json.loads(raw_json)
        return res['inventory']

    async def get_inventory(self) -> List[InventoryItem]:
        return [InventoryItem.from_raw_item(item) for item in await self.get_raw_inventory()]

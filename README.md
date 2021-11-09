# bakkes-rcon

Client for interacting with [BakkesMod](https://bakkesmod.com/) over its websocket RCON.


# Installation

```shell
pip install bakkes-rcon
```


# Usage

```python
import asyncio
from bakkes_rcon import BakkesRconClient

async def main():
    # By default, connects to ws://127.0.0.1:9002, with password "password"
    async with BakkesRconClient() as client:
        inventory = await client.get_inventory()
        for item in inventory:
            print(item)

asyncio.run(main())
```

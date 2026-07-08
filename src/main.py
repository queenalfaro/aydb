
import asyncio 
import json

from youdo import Client


async def main() -> None:
    client = await Client.create()

    result = client.get_config()
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(f, result, indent=4)

    # await client.start_listener()


if __name__ == "__main__":
    asyncio.run(main())

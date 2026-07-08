
import asyncio 

from youdo import Client


async def main() -> None:

    client = await Client.create()
    await client.start_listener()


if __name__ == "__main__":
    asyncio.run(main())

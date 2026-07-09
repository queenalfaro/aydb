
import logging
import asyncio

import config
import formatter
import telegram
from youdo import Client

logger = logging.getLogger(__name__)


def transform_task_data(input_data: dict) -> dict:
    task_data = input_data.get("ResultObject", {})

    subcategory_pack = task_data.get("SubcategoryPackInfo") or {}
    subcategory = subcategory_pack.get("Subcategory") or {}
    subcategory_name = subcategory.get("Name")

    creator_name = task_data.get("CreatorName")
    if not creator_name:
        creator_name = (task_data.get("Creator") or {}).get("FirstName")

    price_string = task_data.get("PriceString", "")
    price_currency = None
    if price_string and " " in price_string:
        price_currency = price_string.split()[-1]

    return {
        "id": task_data.get("Id"),
        "title": task_data.get("Name"),
        "description": task_data.get("Description"),
        "privateInfo": task_data.get("PrivateInfo"),
        "categoryName": task_data.get("CategoryName"),
        "subCategoryName": subcategory_name,
        "creatorAge": None,
        "creatorName": creator_name,
        "price": task_data.get("OwnBudget"),
        "priceCurrency": price_currency,
    }


async def main() -> None:
    logger.info("Bot started")
    client = await Client.create()

    async for raw_new_task in client.start_listener():
        task_id = raw_new_task[0]["id"]
        raw_new_task = client.get_task(task_id)
        new_task_dict = transform_task_data(raw_new_task)
        new_task_text = formatter.format_task(new_task_dict)
        telegram.send_message(new_task_text)


if __name__ == "__main__":
    asyncio.run(main())

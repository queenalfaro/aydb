"""
YouDo task → Telegram HTML message formatter
parse_mode="HTML" + expandable blockquote (Bot API 7.0+)
"""

import html

import config


# ─── helpers ──────────────────────────────────────────────────────────────────

def _esc(text) -> str:
    """Escape HTML special characters for Telegram."""
    return html.escape(str(text))


def _fmt_price(amount, currency: str) -> str:
    """Format price with narrow no-break space thousands separator."""
    try:
        formatted = f"{int(amount):,}".replace(",", "\u202f")
        return f"{formatted} {currency}"
    except (ValueError, TypeError):
        return f"{amount} {currency}".strip()


def _shorten(text: str, limit: int = config.TG_MESSAGE_SHORTEN_LIMIT) -> str:
    """
    Trim description to `limit` chars, preferring paragraph/sentence
    boundaries. Appends ellipsis if truncated.
    """
    text = text.strip()
    if not limit or len(text) <= limit:
        return text

    chunk = text[:limit]

    # Prefer double newline (paragraph), then single, then space
    for sep in ("\n\n", "\n", ". ", " "):
        idx = chunk.rfind(sep)
        if idx != -1 and idx >= limit * 0.55:
            return chunk[:idx].rstrip(".,;:—– ") + "…"

    return chunk.rstrip(".,;:—– ") + "…"


# ─── main formatter ───────────────────────────────────────────────────────────

def format_task(task: dict) -> str:
    """
    Format a raw YouDo task dict into a Telegram HTML message.

    Usage:
        text = format_task(task_dict)
        await bot.send_message(chat_id, text, parse_mode="HTML")
    """
    task_id = task.get("id", "")
    url = f"https://youdo.com/t{task_id}"

    title = task.get("title", "—")
    desc = task.get("description", "")
    category = task.get("categoryName", "—")
    subcat = task.get("subCategoryName", "")
    creator = task.get("creatorName", "—")
    age = task.get("creatorAge")
    price = task.get("price")
    currency = task.get("priceCurrency", "")

    # ── formatted fields ─────────────────────────────────────────────────────
    price_str = _fmt_price(price, currency) if price else "не указан"

    cat_parts = [_esc(category)]
    if subcat:
        cat_parts.append(_esc(subcat))
    cat_line = " › ".join(cat_parts)

    creator_parts = [_esc(creator)]
    if age:
        creator_parts.append(f"{_esc(age)}")
    creator_line = ", ".join(creator_parts)

    short_desc = _esc(_shorten(desc))

    # ── assemble message ──────────────────────────────────────────────────────
    lines = [
        f"<b>{_esc(title)}</b>",
        "",
        f"💰 <b>Бюджет:</b>  {_esc(price_str)}",
        f"📂 <b>Категория:</b>  {cat_line}",
        f"👤 <b>Заказчик:</b>  {creator_line}",
        "",
        f"<blockquote expandable>{short_desc}</blockquote>",
        "",
        f'<a href="{url}">→ Открыть задачу</a>',
    ]
    return "\n".join(lines)


# ─── demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = {
        "id": "14851972",
        "title": "Ищем Python-разработчика: разобраться в готовых скриптах "
                 "(Telegram-боты + API биржи) и устранить ошибки",
        "description": (
            "Привет! Мы команда в сфере крипты и инвестиций. "
            "Продукт работает, аудитория растёт, процессы упорядочены, "
            "без хаоса и микроменеджмента.\n\n"
            "Ищем разработчика на проектную работу с перспективой постоянного "
            "сотрудничества: задачи появляются регулярно, и нам нужен человек, "
            "к которому будем возвращаться снова и снова. "
            "Это не разовый заказ — это вход в долгое сотрудничество.\n\n"
            "Суть: два готовых скрипта от предыдущего разработчика. "
            "Нужно поднять на сервере, разобраться в коде и устранить ошибки.\n\n"
            "Оплата: $150 за обе задачи. Карта РФ или крипта."
        ),
        "categoryName": "Разработка ПО",
        "subCategoryName": "Скрипты и боты",
        "creatorAge": 33,
        "creatorName": "Ангелина И.",
        "price": 15000,
        "priceCurrency": "руб.",
    }

    print(format_task(sample))
    print()
    print("─" * 60)
    print("Отправка: bot.send_message(chat_id, text, parse_mode='HTML')")

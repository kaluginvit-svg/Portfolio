import logging
from typing import List, Optional

import aiohttp

logger = logging.getLogger(__name__)


async def fetch_json(url: str) -> Optional[dict]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    logger.warning("HTTP %s for %s", resp.status, url)
                    return None
                return await resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Request failed for %s: %s", url, exc)
        return None


def render_meal_text(meal: dict) -> str:
    name = meal.get("strMeal") or "Без названия"
    area = meal.get("strArea") or ""
    category = meal.get("strCategory") or ""
    parts = [f"🍲 <b>{name}</b>"]
    if area:
        parts.append(f"Кухня: {area}")
    if category:
        parts.append(f"Категория: {category}")
    parts.append("\nНажмите кнопку ниже для подробностей 👇")
    return "\n".join(parts)


def extract_ingredients(meal: dict) -> List[str]:
    items: List[str] = []
    for idx in range(1, 21):
        ing = meal.get(f"strIngredient{idx}")
        meas = meal.get(f"strMeasure{idx}")
        if ing and ing.strip():
            part = ing.strip()
            if meas and meas.strip():
                part = f"{meas.strip()} {part}".strip()
            items.append(part)
    return items


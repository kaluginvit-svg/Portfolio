from typing import Dict

SEARCH_MODE: Dict[int, bool] = {}
FAVORITES: Dict[int, Dict[str, Dict[str, object]]] = {}
AI_AGENT_CHOICE: Dict[int, str] = {}  # "openrouter", "chutes" или "gigachat" по пользователю

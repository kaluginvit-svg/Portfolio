"""
Настройка логирования и callback для трассировки шагов LangChain (цепочки, LLM, инструменты).
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

_LOG_ROOT_NAME = "local_agent"


def truncate(s: str, max_len: int = 2000) -> str:
    s = s.replace("\r\n", "\n").strip()
    if len(s) <= max_len:
        return s
    return s[:max_len] + f"\n... [обрезано, всего символов: {len(s)}]"


def setup_logging(agent_dir: Path, *, verbose: bool = False) -> logging.Logger:
    """
    Консоль: INFO (или DEBUG при verbose / AGENT_LOG_CONSOLE=DEBUG).
    Файл agent/logs/agent.log: DEBUG, ротация ~5 МБ.
    """
    log = logging.getLogger(_LOG_ROOT_NAME)
    if log.handlers:
        return log

    log.setLevel(logging.DEBUG)
    log.propagate = False

    log_dir = agent_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "agent.log"

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler(sys.stderr)
    console_level = os.getenv("AGENT_LOG_CONSOLE", "").upper().strip()
    if console_level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        ch.setLevel(getattr(logging, console_level))
    else:
        ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(fmt)

    log.addHandler(fh)
    log.addHandler(ch)

    # Шум сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    log.info("Логи: файл %s", log_path)
    return log


def get_trace_callback() -> AgentTracingCallbackHandler:
    return AgentTracingCallbackHandler()


class AgentTracingCallbackHandler(BaseCallbackHandler):
    """Подробные шаги агента: chain / chat_model / LLM / tool / agent_action."""

    def __init__(self) -> None:
        super().__init__()
        self._log = logging.getLogger(f"{_LOG_ROOT_NAME}.trace")

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        name = (serialized or {}).get("name") or (serialized or {}).get("id") or "chain"
        keys = list(inputs.keys()) if isinstance(inputs, dict) else []
        self._log.debug(
            "chain_start run_id=%s name=%s input_keys=%s",
            run_id,
            name,
            keys,
        )
        if isinstance(inputs, dict):
            inp = dict(inputs)
            if "chat_history" in inp and inp["chat_history"] is not None:
                ch = inp["chat_history"]
                inp["chat_history"] = f"<{len(ch)} сообщ.>"
            if "input" in inp and isinstance(inp["input"], str):
                inp["input"] = truncate(inp["input"], 1500)
            self._log.debug("chain_start inputs=%s", truncate(repr(inp), 4000))

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        out = outputs
        if isinstance(out, dict) and "output" in out:
            self._log.debug(
                "chain_end run_id=%s output=%s",
                run_id,
                truncate(str(out.get("output")), 3000),
            )
        else:
            self._log.debug("chain_end run_id=%s outputs=%s", run_id, truncate(repr(out), 3000))

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._log.error(
            "chain_error run_id=%s: %s",
            run_id,
            error,
            exc_info=(type(error), error, error.__traceback__),
        )

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        name = (serialized or {}).get("name") or "chat_model"
        preview_lines: list[str] = []
        for batch in messages or []:
            for m in batch:
                role = getattr(m, "type", type(m).__name__)
                content = getattr(m, "content", "")
                if not isinstance(content, str):
                    content = repr(content)
                preview_lines.append(f"{role}: {truncate(content, 1200)}")
        self._log.debug(
            "chat_model_start run_id=%s model=%s messages:\n%s",
            run_id,
            name,
            truncate("\n---\n".join(preview_lines), 8000),
        )

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        name = (serialized or {}).get("name") or "llm"
        joined = "\n---\n".join(truncate(p, 2000) for p in (prompts or [])[:3])
        if len(prompts or []) > 3:
            joined += f"\n... и ещё {len(prompts) - 3} prompt(s)"
        self._log.debug("llm_start run_id=%s name=%s\n%s", run_id, name, joined)

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        gens = response.generations or []
        texts: list[str] = []
        for g in gens[:5]:
            for t in g:
                texts.append(truncate(getattr(t, "text", "") or str(t), 2000))
        usage = (response.llm_output or {}) if response.llm_output else {}
        self._log.debug(
            "llm_end run_id=%s token_usage=%s preview=%s",
            run_id,
            usage.get("token_usage") or usage,
            truncate("\n".join(texts), 4000),
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self._log.error(
            "llm_error run_id=%s: %s",
            run_id,
            error,
            exc_info=(type(error), error, error.__traceback__),
        )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        name = (serialized or {}).get("name") or "tool"
        self._log.info(
            "tool_start run_id=%s name=%s input=%s",
            run_id,
            name,
            truncate(input_str or "", 4000),
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._log.info(
            "tool_end run_id=%s output=%s",
            run_id,
            truncate(str(output), 6000),
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._log.error(
            "tool_error run_id=%s: %s",
            run_id,
            error,
            exc_info=(type(error), error, error.__traceback__),
        )

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._log.info(
            "agent_action run_id=%s tool=%s tool_input=%s log=%s",
            run_id,
            getattr(action, "tool", None),
            truncate(str(getattr(action, "tool_input", "")), 2000),
            truncate(str(getattr(action, "log", "")), 1500),
        )

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._log.info(
            "agent_finish run_id=%s return_values=%s",
            run_id,
            truncate(str(getattr(finish, "return_values", {})), 3000),
        )

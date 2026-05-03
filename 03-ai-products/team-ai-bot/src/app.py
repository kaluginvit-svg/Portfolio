from __future__ import annotations

import logging
import os

from src.config import Settings
from src.domain.session_manager import SessionManager
from src.logging_config import configure_logging
from src.pipelines.manager import PipelineManager
from src.services.answer_service import AnswerService
from src.services.message_service import MessageService
from src.services.summary_service import SummaryService
from src.storage.local_state import LocalStateStore
from src.telegram_bot import TeamAIBot

logger = logging.getLogger(__name__)


def build_bot() -> TeamAIBot:
    settings = Settings.from_env()
    settings.validate_embedding_dimension()
    configure_logging(settings.log_level)

    # Some Haystack components prefer environment variables even when we pass Secret objects.
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    os.environ["PINECONE_API_KEY"] = settings.pinecone_api_key

    logger.info("Initializing local state at %s", settings.state_db_path)
    state_store = LocalStateStore(settings.state_db_path)
    session_manager = SessionManager(state_store)
    pipeline_manager = PipelineManager(settings)

    message_service = MessageService(session_manager, state_store, pipeline_manager)
    answer_service = AnswerService(pipeline_manager, state_store)
    summary_service = SummaryService(pipeline_manager, state_store)

    return TeamAIBot(
        settings=settings,
        session_manager=session_manager,
        message_service=message_service,
        answer_service=answer_service,
        summary_service=summary_service,
    )


def main() -> None:
    bot = build_bot()
    bot.run()

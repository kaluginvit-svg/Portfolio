from __future__ import annotations

import logging
from typing import Any

import telebot

from src.config import Settings
from src.domain.session_manager import SessionManager
from src.services.answer_service import AnswerService
from src.services.message_service import MessageService
from src.services.summary_service import SummaryService
from src.utils.text import clean_text, truncate_for_telegram

logger = logging.getLogger(__name__)


HELP_TEXT = """Команды бота:
/start или /help - справка
/start_listening - начать запись обсуждения
/stop_listening - завершить запись и получить итог
/status - статус текущей сессии
/ask <вопрос> - задать вопрос по сохраненному контексту

В группе можно также упомянуть бота: @bot_username Что думаешь?
Важно: для чтения всех сообщений в группе отключите Privacy Mode у бота через BotFather."""


class TeamAIBot:
    def __init__(
        self,
        settings: Settings,
        session_manager: SessionManager,
        message_service: MessageService,
        answer_service: AnswerService,
        summary_service: SummaryService,
    ) -> None:
        self.settings = settings
        self.session_manager = session_manager
        self.message_service = message_service
        self.answer_service = answer_service
        self.summary_service = summary_service
        self.bot = telebot.TeleBot(settings.telegram_bot_token, parse_mode=None)
        self.bot_username = ""
        self._register_handlers()

    def run(self) -> None:
        me = self.bot.get_me()
        self.bot_username = getattr(me, "username", "") or ""
        logger.info("Bot started as @%s", self.bot_username)
        self.bot.infinity_polling(skip_pending=True)

    def _register_handlers(self) -> None:
        @self.bot.message_handler(commands=["start", "help"])
        def handle_help(message: Any) -> None:
            if not self._is_allowed_chat(message):
                return
            self._reply(message, HELP_TEXT)

        @self.bot.message_handler(commands=["start_listening"])
        def handle_start_listening(message: Any) -> None:
            if not self._is_allowed_chat(message):
                return
            result = self.session_manager.start(int(message.chat.id))
            if result.already_active:
                self._reply(
                    message,
                    "Запись уже идет.\n"
                    f"session_id: {result.session.session_id}\n"
                    f"сообщений: {result.session.message_count}",
                )
                return
            logger.info("Started listening session %s", result.session.session_id)
            self._reply(
                message,
                "Начал запись обсуждения.\n"
                f"session_id: {result.session.session_id}\n"
                "Теперь все обычные сообщения будут сохраняться в Pinecone.",
            )

        @self.bot.message_handler(commands=["stop_listening"])
        def handle_stop_listening(message: Any) -> None:
            if not self._is_allowed_chat(message):
                return
            session = self.session_manager.stop(int(message.chat.id))
            if session is None:
                self._reply(message, "Активной сессии записи нет. Запустите /start_listening.")
                return
            self._reply(message, "Останавливаю запись и готовлю итог обсуждения...")
            try:
                summary = self.summary_service.summarize_session(session)
            except Exception:
                logger.exception("Failed to summarize session %s", session.session_id)
                self._reply(message, "Сессию остановил, но summary не удалось сформировать. Подробности в логах.")
                return
            self._reply(message, summary)

        @self.bot.message_handler(commands=["status"])
        def handle_status(message: Any) -> None:
            if not self._is_allowed_chat(message):
                return
            session = self.session_manager.status(int(message.chat.id))
            if session is None:
                self._reply(message, "Запись сейчас не идет. Используйте /start_listening.")
                return
            self._reply(
                message,
                "Запись активна.\n"
                f"session_id: {session.session_id}\n"
                f"сообщений: {session.message_count}\n"
                f"старт: {session.started_at.isoformat()}",
            )

        @self.bot.message_handler(commands=["ask"])
        def handle_ask(message: Any) -> None:
            if not self._is_allowed_chat(message):
                return
            parts = (message.text or "").split(maxsplit=1)
            question = clean_text(parts[1] if len(parts) > 1 else "")
            if not question:
                self._reply(message, "Напишите вопрос после команды: /ask Какие решения приняли?")
                return
            self._answer_question(message, question)

        @self.bot.message_handler(content_types=["text"])
        def handle_text(message: Any) -> None:
            if not self._is_allowed_chat(message):
                return
            text = clean_text(getattr(message, "text", ""))
            if self._is_mention_or_reply(message, text):
                question = self._strip_bot_mention(text)
                if not question:
                    question = "Что думаешь по текущему обсуждению?"
                self._answer_question(message, question)
                return

            try:
                self.message_service.handle_text_message(message)
            except Exception:
                logger.exception("Failed to store Telegram message")
                self._reply(message, "Не смог сохранить сообщение в контекст. Подробности в логах.")

    def _answer_question(self, message: Any, question: str) -> None:
        chat_id = int(message.chat.id)
        session = self.session_manager.status(chat_id)
        session_id = session.session_id if session else None
        self._reply(message, "Думаю по сохраненному контексту...")
        try:
            answer = self.answer_service.answer(chat_id=chat_id, question=question, session_id=session_id)
        except Exception:
            logger.exception("Failed to answer question")
            self._reply(message, "Не смог ответить по контексту. Подробности в логах.")
            return
        self._reply(message, answer)

    def _reply(self, message: Any, text: str) -> None:
        safe_text = truncate_for_telegram(text or "Пустой ответ модели.", self.settings.max_telegram_message_length)
        self.bot.reply_to(message, safe_text)

    def _is_allowed_chat(self, message: Any) -> bool:
        if not self.settings.allowed_chat_ids:
            return True
        chat_id = int(message.chat.id)
        if chat_id in self.settings.allowed_chat_ids:
            return True
        logger.warning("Ignoring message from unauthorized chat_id=%s", chat_id)
        return False

    def _is_mention_or_reply(self, message: Any, text: str) -> bool:
        if self.bot_username and f"@{self.bot_username}".lower() in text.lower():
            return True
        reply_to_message = getattr(message, "reply_to_message", None)
        if reply_to_message is None:
            return False
        reply_user = getattr(reply_to_message, "from_user", None)
        return bool(reply_user and getattr(reply_user, "is_bot", False))

    def _strip_bot_mention(self, text: str) -> str:
        if not self.bot_username:
            return text
        return clean_text(text.replace(f"@{self.bot_username}", "").replace(f"@{self.bot_username.lower()}", ""))

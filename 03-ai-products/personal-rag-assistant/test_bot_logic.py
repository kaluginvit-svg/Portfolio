import unittest

from Haystack.haystack_agent import ConversationBuffer, estimate_vision_input_tokens
from components.messages import should_store_message


class BotLogicTests(unittest.TestCase):
    def test_should_store_message_accepts_normal_text(self) -> None:
        self.assertTrue(should_store_message("Я хочу слетать на Марс летом"))

    def test_should_store_message_rejects_commands_and_junk(self) -> None:
        self.assertFalse(should_store_message("/start"))
        self.assertFalse(should_store_message("ok"))
        self.assertFalse(should_store_message("спасибо"))

    def test_conversation_buffer_keeps_recent_turns_only(self) -> None:
        history = ConversationBuffer(max_turns=2)
        history.append_turn(user_id=1, user_text="Привет", assistant_text="Здравствуйте")
        history.append_turn(user_id=1, user_text="Что такое RAG?", assistant_text="Это retrieval augmented generation")
        history.append_turn(user_id=1, user_text="Покажи собаку", assistant_text="Вот собака")

        messages = history.get_messages(1)
        self.assertEqual(len(messages), 4)
        self.assertIn("Что такое RAG?", messages[0].text)
        self.assertIn("Вот собака", messages[-1].text)

    def test_estimate_vision_tokens(self) -> None:
        self.assertEqual(estimate_vision_input_tokens(detail="low"), 85)
        self.assertEqual(estimate_vision_input_tokens(detail="high", width=1024, height=1024), 765)


if __name__ == "__main__":
    unittest.main()

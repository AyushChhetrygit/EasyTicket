import unittest

from app.services.classification_service import (
    ClassificationError,
    TicketClassificationService,
)
from app.services.mock_ai_service import MockAIService
from config.llm_config import LLMConfig


class TicketClassificationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TicketClassificationService(config=LLMConfig(MOCK_AI_MODE=True))

    def test_mock_billing_ticket(self) -> None:
        result = self.service.analyze_ticket(
            "My payment was deducted but my subscription is inactive."
        )

        self.assertEqual(result.category, "billing")
        self.assertEqual(result.priority, "P1")
        self.assertEqual(result.assigned_team, "Billing Support")

    def test_mock_ambiguous_ticket_returns_valid_structure(self) -> None:
        result = self.service.analyze_ticket(
            "I can't access my profile page, but I also want a refund if it takes too long to fix."
        )

        self.assertGreaterEqual(result.classification_confidence, 0.0)
        self.assertLessEqual(result.classification_confidence, 1.0)
        self.assertTrue(result.reason)

    def test_empty_ticket_raises_classification_error(self) -> None:
        with self.assertRaises(ClassificationError):
            self.service.analyze_ticket("")

    def test_no_api_key_in_mock_mode(self) -> None:
        service = TicketClassificationService(config=LLMConfig(USE_MOCK_AI=True))
        result = service.analyze_ticket("Need invoice help.")
        self.assertEqual(result.category, "billing")

    def test_mock_controlled_failure(self) -> None:
        service = TicketClassificationService(
            config=LLMConfig(USE_MOCK_AI=True),
            mock_ai_service=MockAIService(failure_mode="fail"),
        )
        with self.assertRaises(Exception):
            service.analyze_ticket("Need invoice help.")

    def test_malformed_json_and_retry_behaviour(self) -> None:
        class FlakyService(TicketClassificationService):
            def __init__(self) -> None:
                super().__init__(config=LLMConfig(USE_MOCK_AI=False, GEMINI_API_KEY="test"))
                self.calls = 0

            def _build_client(self):
                return object()

            def _generate_live_response(self, client, payload):
                self.calls += 1
                if self.calls == 1:
                    return "{bad json"
                return (
                    '{"category":"billing","subcategory":"invoice",'
                    '"classification_confidence":0.9,"priority":"P1",'
                    '"assigned_team":"Billing Support","reason":"Invoice issue."}'
                )

        service = FlakyService()
        result = service.analyze_ticket("Invoice problem.")
        self.assertEqual(result.category, "billing")
        self.assertEqual(service.calls, 2)

    def test_controlled_failure_after_retry(self) -> None:
        class BrokenService(TicketClassificationService):
            def __init__(self) -> None:
                super().__init__(config=LLMConfig(USE_MOCK_AI=False, GEMINI_API_KEY="test"))

            def _build_client(self):
                return object()

            def _generate_live_response(self, client, payload):
                return "{bad json"

        with self.assertRaises(ClassificationError):
            BrokenService().analyze_ticket("Invoice problem.")


if __name__ == "__main__":
    unittest.main()

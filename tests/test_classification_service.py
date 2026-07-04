import unittest

from app.services.classification_service import (
    ClassificationError,
    TicketClassificationService,
)
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


if __name__ == "__main__":
    unittest.main()

import unittest

from pydantic import ValidationError

from app.models.ai_schemas import TicketAnalysisResult


class TicketAnalysisSchemaTests(unittest.TestCase):
    def test_expected_ai_analysis_output_validates(self) -> None:
        result = TicketAnalysisResult.model_validate(
            {
                "category": "billing",
                "subcategory": "subscription_activation",
                "classification_confidence": 0.92,
                "priority": "P1",
                "assigned_team": "Billing Support",
                "reason": "Payment was deducted but the subscription remains inactive.",
            }
        )

        self.assertEqual(result.category, "billing")
        self.assertEqual(result.priority, "P1")

    def test_extra_fields_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            TicketAnalysisResult.model_validate(
                {
                    "category": "billing",
                    "subcategory": "subscription_activation",
                    "classification_confidence": 0.92,
                    "priority": "P1",
                    "assigned_team": "Billing Support",
                    "reason": "Payment was deducted but the subscription remains inactive.",
                    "unexpected": "not allowed",
                }
            )


if __name__ == "__main__":
    unittest.main()

import unittest

from app.services.priority_service import PriorityEstimationService
from app.models.ai_schemas import PriorityResult
from config.llm_config import LLMConfig
from pydantic import ValidationError


class PriorityEstimationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PriorityEstimationService(config=LLMConfig(MOCK_AI_MODE=True))

    def test_complete_outage_is_p0(self) -> None:
        result = self.service.estimate_priority("Complete outage, all users are down.")
        self.assertEqual(result.priority, "P0")

    def test_business_critical_access_issue_is_p1(self) -> None:
        result = self.service.estimate_priority(
            "Admin users are blocked and cannot access the dashboard.",
            {"plan": "Enterprise"},
        )
        self.assertEqual(result.priority, "P1")

    def test_issue_with_workaround_is_p2(self) -> None:
        result = self.service.estimate_priority(
            "Export is broken, but CSV download is an available workaround."
        )
        self.assertEqual(result.priority, "P2")

    def test_normal_issue_is_p3(self) -> None:
        result = self.service.estimate_priority("The settings page loads slowly.")
        self.assertEqual(result.priority, "P3")

    def test_low_impact_feature_request_is_p4(self) -> None:
        result = self.service.estimate_priority("Feature request: add a new theme.")
        self.assertEqual(result.priority, "P4")

    def test_valid_priority_output(self) -> None:
        result = PriorityResult.model_validate({"priority": "P2", "reason": "Workaround exists."})
        self.assertEqual(result.priority, "P2")

    def test_invalid_priority_rejection(self) -> None:
        with self.assertRaises(ValidationError):
            PriorityResult.model_validate({"priority": "P9", "reason": "Invalid."})


if __name__ == "__main__":
    unittest.main()

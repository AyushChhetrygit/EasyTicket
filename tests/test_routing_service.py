import unittest

from app.services.routing_service import TeamRoutingService
from config.llm_config import LLMConfig


class TeamRoutingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TeamRoutingService(config=LLMConfig(MOCK_AI_MODE=True))

    def test_account_routes_to_account_support(self) -> None:
        result = self.service.route_ticket("Cannot log in.", "account", "login", "P2")
        self.assertEqual(result.assigned_team, "Account Support")

    def test_billing_routes_to_billing_support(self) -> None:
        result = self.service.route_ticket("Invoice is wrong.", "billing", "invoice", "P3")
        self.assertEqual(result.assigned_team, "Billing Support")

    def test_refund_routes_to_billing_support(self) -> None:
        result = self.service.route_ticket("Need refund.", "refund", "refund_request", "P3")
        self.assertEqual(result.assigned_team, "Billing Support")

    def test_technical_routes_to_technical_support(self) -> None:
        result = self.service.route_ticket("Button fails.", "technical", "bug", "P3")
        self.assertEqual(result.assigned_team, "Technical Support")

    def test_feature_request_routes_to_product_team(self) -> None:
        result = self.service.route_ticket("Add export.", "feature_request", "export", "P4")
        self.assertEqual(result.assigned_team, "Product Team")

    def test_high_priority_override_routes_to_engineering(self) -> None:
        result = self.service.route_ticket("All users down.", "technical", "outage", "P0")
        self.assertEqual(result.assigned_team, "Engineering")


if __name__ == "__main__":
    unittest.main()

import unittest
import time

from app.workflows.ticket_analysis_workflow import (
    TicketAnalysisWorkflowError,
    analyze_ticket,
)


class TicketAnalysisWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_analyze_ticket_returns_combined_result(self) -> None:
        result = await analyze_ticket(
            {"message": "My payment was deducted but my subscription is inactive."},
            {"plan": "Enterprise"},
            timeout_seconds=5,
        )

        self.assertEqual(result.category, "billing")
        self.assertEqual(result.priority, "P1")
        self.assertEqual(result.assigned_team, "Billing Support")
        self.assertTrue(result.reason)

    async def test_llm_timeout(self) -> None:
        class SlowClassificationService:
            def analyze_ticket(self, ticket_message, customer_info=None):
                time.sleep(0.05)

        with self.assertRaises(TicketAnalysisWorkflowError):
            await analyze_ticket(
                {"message": "Settings page is slow."},
                timeout_seconds=0.001,
                classification_service=SlowClassificationService(),
            )


if __name__ == "__main__":
    unittest.main()

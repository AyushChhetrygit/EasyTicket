import unittest

from app.workflows.ticket_analysis_workflow import analyze_ticket


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


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, ANY
from datetime import datetime

# Assuming your project structure for imports
from features.Admin_Panel.admin_dashboard.admin_dashboard_logic import AdminDashboardLogic
from features.Admin_Panel.admin_dashboard.admin_dashboard_repo import AdminDashboardRepository


class TestAdminDashboardLogic(unittest.TestCase):

    def setUp(self):
        """
        Runs before every test. Sets up the mocks.
        """
        # 1. Mock the Repository
        # We replace the real SQL-heavy class with a "dummy" that we control.
        self.mock_repo = MagicMock(spec=AdminDashboardRepository)

        # 2. Mock the Session Provider
        # Since logic uses 'with self._business_session() as session:',
        # we need to mock the context manager behavior.
        self.mock_session = MagicMock()
        self.mock_session_provider = MagicMock()
        self.mock_session_provider.return_value.__enter__.return_value = self.mock_session

        # 3. Initialize the Logic class with our Mocks
        self.logic = AdminDashboardLogic(
            repository=self.mock_repo,
            business_engine=self.mock_session_provider
        )

    def test_get_kpi_data_formats_currency_correctly(self):
        """
        Test that raw numbers from the repo are converted to 'X تومان' strings.
        """
        # Arrange: Tell the mock repo what to return when asked
        self.mock_repo.get_revenue_today.return_value = 50000.0
        self.mock_repo.get_revenue_this_month.return_value = 1200000.0
        self.mock_repo.get_total_outstanding.return_value = 0.0
        self.mock_repo.get_new_customers_this_month.return_value = 5

        # Act: Run the logic method
        kpi_data = self.logic.get_kpi_data()

        # Assert: Verify the Logic did its job (formatting)
        self.assertEqual(kpi_data.revenue_today, "50,000 تومان")
        self.assertEqual(kpi_data.revenue_month, "1,200,000 تومان")

        # Verify the Repo was actually called with our mock session
        self.mock_repo.get_revenue_today.assert_called_once_with(self.mock_session)

    def test_get_attention_queue_stitches_companion_counts(self):
        """
        Test the complex logic where orders are enriched with companion counts.
        This proves why Logic shouldn't be inside the Repo.
        """
        # Arrange: Create fake order objects
        mock_order_1 = MagicMock(national_id="123", invoice_number="INV-001", name="Alice")
        mock_order_2 = MagicMock(national_id="456", invoice_number="INV-002", name="Bob")

        # Setup Repo returns
        self.mock_repo.get_orders_needing_attention.return_value = [mock_order_1, mock_order_2]
        self.mock_repo.get_unpaid_collected_invoices.return_value = []  # Ignore this for this test

        # The critical part: Mocking the companion count dictionary lookup
        # Logic expects: { "123": 2, "456": 0 }
        self.mock_repo.get_companion_counts_for_customers.return_value = {"123": 2}

        # Act
        result = self.logic.get_attention_queue()
        due_orders = result["due_orders"]

        # Assert
        # 1. Check if Logic correctly extracted IDs to call the companion repo method
        self.mock_repo.get_companion_counts_for_customers.assert_called_with(
            self.mock_session, ["123", "456"]
        )

        # 2. Check if data was stitched correctly
        # Alice (123) should have 2 companions (from dict)
        self.assertEqual(due_orders[0].national_id, "123")
        self.assertEqual(due_orders[0].companion_count, 2)

        # Bob (456) was not in the dict, so logic should default to 0
        self.assertEqual(due_orders[1].national_id, "456")
        self.assertEqual(due_orders[1].companion_count, 0)


if __name__ == '__main__':
    unittest.main()

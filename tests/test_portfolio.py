from __future__ import annotations

import unittest
from datetime import datetime

from portfolio.portfolio_manager import PortfolioManager


class TestPortfolioManager(unittest.TestCase):
    
    def setUp(self):
        self.portfolio = PortfolioManager(starting_capital=100000.0)
    
    def test_initial_state(self):
        self.assertEqual(self.portfolio.cash, 100000.0)
        self.assertEqual(len(self.portfolio.open_positions), 0)
    
    def test_buy_option(self):
        success = self.portfolio.execute_order(
            ticker="SPY",
            expiration=datetime(2024, 2, 16),
            strike=450.0,
            option_type="call",
            side="buy",
            quantity=1,
            price=5.00,
            timestamp=datetime(2024, 1, 2)
        )
        
        self.assertTrue(success)
        self.assertEqual(len(self.portfolio.open_positions), 1)
        self.assertEqual(self.portfolio.cash, 100000.0 - 500.0)
    
    def test_buy_insufficient_cash(self):
        success = self.portfolio.execute_order(
            ticker="SPY",
            expiration=datetime(2024, 2, 16),
            strike=450.0,
            option_type="call",
            side="buy",
            quantity=300,
            price=500.00,
            timestamp=datetime(2024, 1, 2)
        )
        
        self.assertFalse(success)
        self.assertEqual(len(self.portfolio.open_positions), 0)
    
    def test_sell_option(self):
        self.portfolio.execute_order(
            ticker="SPY",
            expiration=datetime(2024, 2, 16),
            strike=450.0,
            option_type="call",
            side="buy",
            quantity=1,
            price=5.00,
            timestamp=datetime(2024, 1, 2)
        )
        
        success = self.portfolio.execute_order(
            ticker="SPY",
            expiration=datetime(2024, 2, 16),
            strike=450.0,
            option_type="call",
            side="sell",
            quantity=1,
            price=6.00,
            timestamp=datetime(2024, 1, 3)
        )
        
        self.assertTrue(success)
        self.assertEqual(len(self.portfolio.open_positions), 0)
        self.assertEqual(self.portfolio.cash, 100000.0 - 500.0 + 600.0)
    
    def test_get_total_value(self):
        total = self.portfolio.get_total_value()
        self.assertEqual(total, 100000.0)


if __name__ == '__main__':
    unittest.main()

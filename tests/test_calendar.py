from __future__ import annotations

import unittest
from datetime import datetime

from market.calendar import TradingCalendar


class TestTradingCalendar(unittest.TestCase):
    
    def test_is_trading_day_weekday(self):
        weekday = datetime(2024, 1, 2)
        self.assertTrue(TradingCalendar.is_trading_day(weekday))
    
    def test_is_trading_day_weekend(self):
        saturday = datetime(2024, 1, 6)
        sunday = datetime(2024, 1, 7)
        self.assertFalse(TradingCalendar.is_trading_day(saturday))
        self.assertFalse(TradingCalendar.is_trading_day(sunday))
    
    def test_is_trading_day_holiday(self):
        new_years = datetime(2024, 1, 1)
        self.assertFalse(TradingCalendar.is_trading_day(new_years))
    
    def test_next_trading_day(self):
        friday = datetime(2024, 1, 5)
        next_day = TradingCalendar.next_trading_day(friday)
        self.assertEqual(next_day.weekday(), 0)
    
    def test_generate_trading_days(self):
        start = datetime(2024, 1, 2)
        days = TradingCalendar.generate_trading_days(start, 10)
        
        self.assertEqual(len(days), 10)
        
        for day in days:
            self.assertTrue(TradingCalendar.is_trading_day(day))
    
    def test_get_weekly_expirations(self):
        start = datetime(2024, 1, 2)
        expirations = TradingCalendar.get_weekly_expirations(start, 32)
        
        for exp in expirations:
            self.assertEqual(exp.weekday(), 4)
            self.assertTrue(TradingCalendar.is_trading_day(exp))
    
    def test_get_monthly_expiration(self):
        exp = TradingCalendar.get_monthly_expiration(2024, 1)
        
        self.assertEqual(exp.weekday(), 4)
        self.assertTrue(exp.day >= 15)
        self.assertTrue(exp.day <= 21)


if __name__ == '__main__':
    unittest.main()

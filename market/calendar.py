from __future__ import annotations

from datetime import datetime, timedelta
from typing import List


class TradingCalendar:

    MARKET_HOLIDAYS_2024_2026 = [
        datetime(2024, 1, 1),
        datetime(2024, 1, 15),
        datetime(2024, 2, 19),
        datetime(2024, 3, 29),
        datetime(2024, 5, 27),
        datetime(2024, 6, 19),
        datetime(2024, 7, 4),
        datetime(2024, 9, 2),
        datetime(2024, 11, 28),
        datetime(2024, 12, 25),
        datetime(2025, 1, 1),
        datetime(2025, 1, 20),
        datetime(2025, 2, 17),
        datetime(2025, 4, 18),
        datetime(2025, 5, 26),
        datetime(2025, 6, 19),
        datetime(2025, 7, 4),
        datetime(2025, 9, 1),
        datetime(2025, 11, 27),
        datetime(2025, 12, 25),
        datetime(2026, 1, 1),
        datetime(2026, 1, 19),
        datetime(2026, 2, 16),
        datetime(2026, 4, 3),
        datetime(2026, 5, 25),
        datetime(2026, 6, 19),
        datetime(2026, 7, 3),
        datetime(2026, 9, 7),
        datetime(2026, 11, 26),
        datetime(2026, 12, 25),
    ]

    MARKET_OPEN = datetime.strptime("09:30", "%H:%M").time()
    MARKET_CLOSE = datetime.strptime("16:00", "%H:%M").time()

    @staticmethod
    def is_trading_day(date: datetime) -> bool:
        date_only = date.date()
        if date_only.weekday() >= 5:
            return False
        for holiday in TradingCalendar.MARKET_HOLIDAYS_2024_2026:
            if holiday.date() == date_only:
                return False
        return True

    @staticmethod
    def next_trading_day(date: datetime) -> datetime:
        next_day = date + timedelta(days=1)
        while not TradingCalendar.is_trading_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    @staticmethod
    def generate_trading_days(start_date: datetime, n_days: int) -> List[datetime]:
        trading_days = []
        current_date = start_date

        if not TradingCalendar.is_trading_day(current_date):
            current_date = TradingCalendar.next_trading_day(current_date)

        for _ in range(n_days):
            trading_days.append(current_date)
            current_date = TradingCalendar.next_trading_day(current_date)

        return trading_days

    @staticmethod
    def get_weekly_expirations(start_date: datetime, max_dte: int) -> List[datetime]:
        expirations = []
        current_date = start_date
        end_date = start_date + timedelta(days=max_dte)

        while current_date <= end_date:
            if current_date.weekday() == 4:
                if TradingCalendar.is_trading_day(current_date):
                    expiration_date = datetime.combine(current_date.date(), datetime.min.time())
                    expirations.append(expiration_date)
            current_date += timedelta(days=1)

        return expirations

    @staticmethod
    def get_monthly_expiration(year: int, month: int) -> datetime:
        first_day = datetime(year, month, 1)

        third_friday_day = 1
        fridays_found = 0
        while fridays_found < 3:
            test_date = datetime(year, month, third_friday_day)
            if test_date.weekday() == 4:
                fridays_found += 1
                if fridays_found == 3:
                    if TradingCalendar.is_trading_day(test_date):
                        return test_date
                    else:
                        prev_day = test_date - timedelta(days=1)
                        while not TradingCalendar.is_trading_day(prev_day):
                            prev_day -= timedelta(days=1)
                        return prev_day
            third_friday_day += 1

        raise ValueError(f"Could not find third Friday for {year}-{month}")

    @staticmethod
    def get_expirations_for_date(current_date: datetime) -> List[datetime]:
        expirations = []

        weekly = TradingCalendar.get_weekly_expirations(current_date, 32)
        for exp in weekly:
            if exp.date() > current_date.date():
                expirations.append(exp)
            elif exp.date() == current_date.date():
                market_close = TradingCalendar.get_market_close(current_date)
                if current_date < market_close:
                    expirations.append(exp)

        current_month = current_date.month
        current_year = current_date.year

        for offset in range(0, 4):
            target_month = current_month + offset
            target_year = current_year

            if target_month > 12:
                target_month -= 12
                target_year += 1

            monthly_exp = TradingCalendar.get_monthly_expiration(target_year, target_month)
            if monthly_exp not in expirations:
                if monthly_exp.date() > current_date.date():
                    dte = (monthly_exp - current_date).days
                    if dte >= 40:
                        expirations.append(monthly_exp)
                elif monthly_exp.date() == current_date.date():
                    market_close = TradingCalendar.get_market_close(current_date)
                    if current_date < market_close:
                        dte = (monthly_exp - current_date).days
                        if dte >= 40:
                            expirations.append(monthly_exp)

        return sorted(expirations)

    @staticmethod
    def get_market_open(date: datetime) -> datetime:
        return datetime.combine(date.date(), TradingCalendar.MARKET_OPEN)

    @staticmethod
    def get_market_close(date: datetime) -> datetime:
        return datetime.combine(date.date(), TradingCalendar.MARKET_CLOSE)

from __future__ import annotations

import logging
from datetime import datetime

from portfolio.portfolio_manager import PortfolioManager
from utils.types import OptionQuote, Greeks

logging.basicConfig(level=logging.INFO)


def test_position_initialized_with_entry_price():
    """Test that positions are created with current_price set to entry_price."""
    pm = PortfolioManager(100000.0)
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 1, 5),
        strike=450.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=3.29,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    assert len(pm.open_positions) == 1, "Should have 1 open position"
    pos = pm.open_positions[0]
    
    assert pos.entry_price == 3.29, f"Entry price should be 3.29, got {pos.entry_price}"
    assert pos.current_price == 3.29, f"Current price should be initialized to 3.29, got {pos.current_price}"
    
    pnl = pos.get_pnl()
    assert pnl == 0.0, f"Initial P&L should be 0, got ${pnl:.2f}"
    
    print(f"✓ Position initialized: entry=${pos.entry_price:.2f}, current=${pos.current_price:.2f}, P&L=${pnl:.2f}")


def test_mark_to_market_updates_pnl():
    """Test that mark_to_market updates current_price and P&L."""
    pm = PortfolioManager(100000.0)
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 1, 5),
        strike=450.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=3.29,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    option_chain = [
        OptionQuote(
            ticker="SPY",
            strike=450.0,
            expiration=datetime(2024, 1, 5),
            option_type="put",
            bid=2.50,
            ask=2.70,
            mid=2.60,
            iv=0.15,
            greeks=Greeks(delta=-0.35, gamma=0.02, theta=-0.05, vega=0.10, rho=-0.03)
        )
    ]
    
    pm.update_positions(option_chain)
    
    pos = pm.open_positions[0]
    assert pos.current_price == 2.60, f"Current price should be updated to 2.60, got {pos.current_price}"
    
    pnl = pos.get_pnl()
    expected_pnl = -1 * (2.60 - 3.29) * 100  # +$69
    assert pnl == expected_pnl, f"P&L should be ${expected_pnl:.2f}, got ${pnl:.2f}"
    
    print(f"✓ After MTM update: current=${pos.current_price:.2f}, P&L=${pnl:.2f}")


def test_multiple_positions_mtm():
    """Test mark-to-market with multiple positions."""
    pm = PortfolioManager(100000.0)
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 1, 5),
        strike=450.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=3.29,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 1, 5),
        strike=455.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=4.50,
        timestamp=datetime(2024, 1, 2, 10, 5, 0)
    )
    
    option_chain = [
        OptionQuote(
            ticker="SPY",
            strike=450.0,
            expiration=datetime(2024, 1, 5),
            option_type="put",
            bid=2.50,
            ask=2.70,
            mid=2.60,
            iv=0.15,
            greeks=Greeks(delta=-0.35, gamma=0.02, theta=-0.05, vega=0.10, rho=-0.03)
        ),
        OptionQuote(
            ticker="SPY",
            strike=455.0,
            expiration=datetime(2024, 1, 5),
            option_type="put",
            bid=3.80,
            ask=4.00,
            mid=3.90,
            iv=0.16,
            greeks=Greeks(delta=-0.40, gamma=0.02, theta=-0.06, vega=0.11, rho=-0.04)
        )
    ]
    
    pm.update_positions(option_chain)
    
    pos1 = [p for p in pm.open_positions if p.strike == 450.0][0]
    pos2 = [p for p in pm.open_positions if p.strike == 455.0][0]
    
    assert pos1.current_price == 2.60, f"Pos1 current price should be 2.60, got {pos1.current_price}"
    assert pos2.current_price == 3.90, f"Pos2 current price should be 3.90, got {pos2.current_price}"
    
    pnl1 = pos1.get_pnl()
    pnl2 = pos2.get_pnl()
    
    expected_pnl1 = -1 * (2.60 - 3.29) * 100  # +$69
    expected_pnl2 = -1 * (3.90 - 4.50) * 100  # +$60
    
    assert pnl1 == expected_pnl1, f"Pos1 P&L should be ${expected_pnl1:.2f}, got ${pnl1:.2f}"
    assert pnl2 == expected_pnl2, f"Pos2 P&L should be ${expected_pnl2:.2f}, got ${pnl2:.2f}"
    
    total_pnl = pnl1 + pnl2
    print(f"✓ Multiple positions: Pos1 P&L=${pnl1:.2f}, Pos2 P&L=${pnl2:.2f}, Total=${total_pnl:.2f}")


def test_position_not_in_chain():
    """Test P&L when position's option is not in the current chain."""
    pm = PortfolioManager(100000.0)
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 1, 5),
        strike=450.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=3.29,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    option_chain = [
        OptionQuote(
            ticker="SPY",
            strike=455.0,
            expiration=datetime(2024, 1, 5),
            option_type="put",
            bid=3.80,
            ask=4.00,
            mid=3.90,
            iv=0.16,
            greeks=Greeks(delta=-0.40, gamma=0.02, theta=-0.06, vega=0.11, rho=-0.04)
        )
    ]
    
    pm.update_positions(option_chain)
    
    pos = pm.open_positions[0]
    assert pos.current_price == 3.29, f"Current price should remain at entry 3.29, got {pos.current_price}"
    
    pnl = pos.get_pnl()
    assert pnl == 0.0, f"P&L should be 0 when not updated, got ${pnl:.2f}"
    
    print(f"✓ Position not in chain: current=${pos.current_price:.2f}, P&L=${pnl:.2f}")


if __name__ == "__main__":
    print("Running portfolio mark-to-market tests...\n")
    
    try:
        test_position_initialized_with_entry_price()
    except AssertionError as e:
        print(f"✗ test_position_initialized_with_entry_price failed: {e}")
    
    try:
        test_mark_to_market_updates_pnl()
    except AssertionError as e:
        print(f"✗ test_mark_to_market_updates_pnl failed: {e}")
    
    try:
        test_multiple_positions_mtm()
    except AssertionError as e:
        print(f"✗ test_multiple_positions_mtm failed: {e}")
    
    try:
        test_position_not_in_chain()
    except AssertionError as e:
        print(f"✗ test_position_not_in_chain failed: {e}")
    
    print("\nAll tests completed!")

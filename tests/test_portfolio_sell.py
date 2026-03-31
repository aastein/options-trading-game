from __future__ import annotations

import logging
from datetime import datetime

from portfolio.portfolio_manager import PortfolioManager

logging.basicConfig(level=logging.INFO)


def test_buy_to_open():
    """Test buying an option (buy-to-open)."""
    pm = PortfolioManager(100000.0)
    
    success = pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        side="buy",
        quantity=1,
        price=3.50,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    assert success, "Buy-to-open should succeed"
    assert len(pm.open_positions) == 1, "Should have 1 open position"
    assert pm.open_positions[0].quantity == 1, "Position quantity should be 1"
    assert pm.cash == 100000.0 - (3.50 * 100), "Cash should be reduced by option cost"
    print("✓ test_buy_to_open passed")


def test_sell_to_open():
    """Test selling an option without owning it (sell-to-open / short)."""
    pm = PortfolioManager(100000.0)
    
    success = pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=3.50,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    assert success, "Sell-to-open should succeed"
    assert len(pm.open_positions) == 1, "Should have 1 open position"
    assert pm.open_positions[0].quantity == -1, "Position quantity should be -1 (short)"
    assert pm.cash == 100000.0 + (3.50 * 100), "Cash should be increased by premium received"
    print("✓ test_sell_to_open passed")


def test_sell_to_close():
    """Test selling an option to close an existing long position."""
    pm = PortfolioManager(100000.0)
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        side="buy",
        quantity=2,
        price=3.50,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    success = pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=4.00,
        timestamp=datetime(2024, 1, 2, 11, 0, 0)
    )
    
    assert success, "Sell-to-close should succeed"
    assert len(pm.open_positions) == 1, "Should still have 1 open position"
    assert pm.open_positions[0].quantity == 1, "Position quantity should be reduced to 1"
    expected_cash = 100000.0 - (3.50 * 2 * 100) + (4.00 * 100)
    assert pm.cash == expected_cash, f"Cash should be {expected_cash}, got {pm.cash}"
    print("✓ test_sell_to_close passed")


def test_buy_to_close():
    """Test buying an option to close an existing short position."""
    pm = PortfolioManager(100000.0)
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        side="sell",
        quantity=2,
        price=3.50,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    success = pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        side="buy",
        quantity=1,
        price=3.00,
        timestamp=datetime(2024, 1, 2, 11, 0, 0)
    )
    
    assert success, "Buy-to-close should succeed"
    assert len(pm.open_positions) == 1, "Should still have 1 open position"
    assert pm.open_positions[0].quantity == -1, "Position quantity should be reduced to -1"
    expected_cash = 100000.0 + (3.50 * 2 * 100) - (3.00 * 100)
    assert pm.cash == expected_cash, f"Cash should be {expected_cash}, got {pm.cash}"
    print("✓ test_buy_to_close passed")


def test_multiple_positions():
    """Test multiple independent positions."""
    pm = PortfolioManager(100000.0)
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=3.50,
        timestamp=datetime(2024, 1, 2, 10, 0, 0)
    )
    
    pm.execute_order(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=455.0,
        option_type="put",
        side="sell",
        quantity=1,
        price=4.00,
        timestamp=datetime(2024, 1, 2, 10, 5, 0)
    )
    
    assert len(pm.open_positions) == 2, "Should have 2 open positions"
    assert pm.cash == 100000.0 + (3.50 * 100) + (4.00 * 100), "Cash should reflect both premiums"
    print("✓ test_multiple_positions passed")


if __name__ == "__main__":
    print("Running portfolio sell tests...\n")
    
    try:
        test_buy_to_open()
    except AssertionError as e:
        print(f"✗ test_buy_to_open failed: {e}")
    
    try:
        test_sell_to_open()
    except AssertionError as e:
        print(f"✗ test_sell_to_open failed: {e}")
    
    try:
        test_sell_to_close()
    except AssertionError as e:
        print(f"✗ test_sell_to_close failed: {e}")
    
    try:
        test_buy_to_close()
    except AssertionError as e:
        print(f"✗ test_buy_to_close failed: {e}")
    
    try:
        test_multiple_positions()
    except AssertionError as e:
        print(f"✗ test_multiple_positions failed: {e}")
    
    print("\nAll tests completed!")

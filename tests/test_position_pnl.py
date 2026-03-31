from __future__ import annotations

from datetime import datetime

from utils.types import Position


def test_long_position_profit():
    """Test P&L calculation for profitable long position."""
    pos = Position(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        quantity=1,
        entry_price=3.00,
        entry_timestamp=datetime(2024, 1, 2, 10, 0, 0),
        current_price=4.00
    )
    
    pnl = pos.get_pnl()
    expected = 1 * (4.00 - 3.00) * 100  # +$100
    assert pnl == expected, f"Expected ${expected}, got ${pnl}"
    print(f"✓ Long position profit: ${pnl:.2f}")


def test_long_position_loss():
    """Test P&L calculation for losing long position."""
    pos = Position(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        quantity=2,
        entry_price=5.00,
        entry_timestamp=datetime(2024, 1, 2, 10, 0, 0),
        current_price=3.50
    )
    
    pnl = pos.get_pnl()
    expected = 2 * (3.50 - 5.00) * 100  # -$300
    assert pnl == expected, f"Expected ${expected}, got ${pnl}"
    print(f"✓ Long position loss: ${pnl:.2f}")


def test_short_position_profit():
    """Test P&L calculation for profitable short position."""
    pos = Position(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        quantity=-1,  # Short position
        entry_price=3.29,
        entry_timestamp=datetime(2024, 1, 2, 10, 0, 0),
        current_price=2.00
    )
    
    pnl = pos.get_pnl()
    expected = -1 * (2.00 - 3.29) * 100  # +$129
    assert pnl == expected, f"Expected ${expected:.2f}, got ${pnl:.2f}"
    print(f"✓ Short position profit: ${pnl:.2f}")


def test_short_position_loss():
    """Test P&L calculation for losing short position."""
    pos = Position(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        quantity=-2,  # Short position
        entry_price=3.00,
        entry_timestamp=datetime(2024, 1, 2, 10, 0, 0),
        current_price=5.00
    )
    
    pnl = pos.get_pnl()
    expected = -2 * (5.00 - 3.00) * 100  # -$400
    assert pnl == expected, f"Expected ${expected}, got ${pnl}"
    print(f"✓ Short position loss: ${pnl:.2f}")


def test_mark_to_market():
    """Test mark-to-market price update."""
    pos = Position(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        quantity=-1,
        entry_price=3.29,
        entry_timestamp=datetime(2024, 1, 2, 10, 0, 0),
        current_price=0.0  # Initial
    )
    
    assert pos.current_price == 0.0, "Initial current_price should be 0.0"
    
    pos.mark_to_market(2.50)
    assert pos.current_price == 2.50, "Current price should be updated to 2.50"
    
    pnl = pos.get_pnl()
    expected = -1 * (2.50 - 3.29) * 100  # +$79
    assert pnl == expected, f"Expected ${expected:.2f}, got ${pnl:.2f}"
    print(f"✓ Mark-to-market update: current=${pos.current_price:.2f}, P&L=${pnl:.2f}")


def test_zero_pnl():
    """Test zero P&L when current price equals entry price."""
    pos = Position(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        quantity=-1,
        entry_price=3.29,
        entry_timestamp=datetime(2024, 1, 2, 10, 0, 0),
        current_price=3.29
    )
    
    pnl = pos.get_pnl()
    assert pnl == 0.0, f"Expected $0.00, got ${pnl:.2f}"
    print(f"✓ Zero P&L when prices match: ${pnl:.2f}")


def test_current_price_not_updated():
    """Test P&L when current_price is never updated (stays at 0.0)."""
    pos = Position(
        ticker="SPY",
        expiration=datetime(2024, 2, 16),
        strike=450.0,
        option_type="put",
        quantity=-1,
        entry_price=3.29,
        entry_timestamp=datetime(2024, 1, 2, 10, 0, 0),
        current_price=0.0
    )
    
    pnl = pos.get_pnl()
    expected = -1 * (0.0 - 3.29) * 100  # +$329 (unrealistic but shows the issue)
    assert pnl == expected, f"Expected ${expected:.2f}, got ${pnl:.2f}"
    print(f"✓ P&L with current_price=0.0: ${pnl:.2f} (WARNING: This indicates current_price not updated)")


if __name__ == "__main__":
    print("Running position P&L tests...\n")
    
    try:
        test_long_position_profit()
    except AssertionError as e:
        print(f"✗ test_long_position_profit failed: {e}")
    
    try:
        test_long_position_loss()
    except AssertionError as e:
        print(f"✗ test_long_position_loss failed: {e}")
    
    try:
        test_short_position_profit()
    except AssertionError as e:
        print(f"✗ test_short_position_profit failed: {e}")
    
    try:
        test_short_position_loss()
    except AssertionError as e:
        print(f"✗ test_short_position_loss failed: {e}")
    
    try:
        test_mark_to_market()
    except AssertionError as e:
        print(f"✗ test_mark_to_market failed: {e}")
    
    try:
        test_zero_pnl()
    except AssertionError as e:
        print(f"✗ test_zero_pnl failed: {e}")
    
    try:
        test_current_price_not_updated()
    except AssertionError as e:
        print(f"✗ test_current_price_not_updated failed: {e}")
    
    print("\nAll tests completed!")

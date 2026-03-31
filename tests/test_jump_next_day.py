from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import GameEngine
from utils.types import Position
from utils.config_loader import ConfigLoader


def test_jump_next_day_updates_pnl():
    """Test that jumping to next day updates position P&L"""

    ticker = "SPY"
    config_loader = ConfigLoader()
    ticker_config = config_loader.load_ticker_config(ticker)
    start_date = datetime(2024, 1, 2)
    engine = GameEngine(
        ticker=ticker,
        starting_capital=100000.0,
        start_date=start_date,
        ticker_config=ticker_config
    )

    initial_spot = engine.current_spot_price
    print(f"\n=== Day 1 ===")
    print(f"Spot price: ${initial_spot:.2f}")
    print(f"Current time: {engine.current_time}")
    print(f"Day index: {engine.current_day_index}")

    option = None
    for opt in engine.option_chain:
        if opt.option_type == "put" and opt.strike == 450.0:
            if opt.expiration.date() > engine.current_time.date():
                option = opt
                break

    assert option is not None, "Could not find suitable option"

    success = engine.portfolio_manager.execute_order(
        ticker=option.ticker,
        expiration=option.expiration,
        strike=option.strike,
        option_type=option.option_type,
        side="sell",
        quantity=1,
        price=option.bid,
        timestamp=engine.current_time
    )

    assert success, "Order execution failed"

    assert len(engine.portfolio_manager.open_positions) == 1
    pos = engine.portfolio_manager.open_positions[0]

    print(f"\nOpened position:")
    print(f"  Expiration: {pos.expiration}")
    print(f"  Strike: ${pos.strike:.2f}")
    print(f"  Type: {pos.option_type}")
    print(f"  Qty: {pos.quantity}")
    print(f"  Entry: ${pos.entry_price:.2f}")
    print(f"  Current: ${pos.current_price:.2f}")
    print(f"  P&L: ${pos.get_pnl():.2f}")

    print(f"\nChecking option chain BEFORE jump:")
    found_match = False
    for opt in engine.option_chain:
        if (opt.strike == pos.strike and
            opt.option_type == pos.option_type and
            opt.expiration == pos.expiration):
            print(f"  ✓ Found matching option: exp={opt.expiration}, mid=${opt.mid:.2f}")
            found_match = True
            break
    if not found_match:
        print(f"  ✗ NO MATCHING OPTION IN CHAIN")
        print(f"  Looking for: strike={pos.strike}, type={pos.option_type}, exp={pos.expiration}")
        print(f"  Chain has {len(engine.option_chain)} options")

    entry_price = float(pos.entry_price)
    initial_current_price = float(pos.current_price)
    initial_pnl = float(pos.get_pnl())

    print(f"\n=== Before Jump ===")
    print(f"Option chain size: {len(engine.option_chain)}")
    matching_option_before = None
    for opt in engine.option_chain:
        if (opt.strike == pos.strike and
            opt.option_type == pos.option_type and
            opt.expiration == pos.expiration):
            matching_option_before = opt
            print(f"Matching option in chain: mid=${opt.mid:.2f}, bid=${opt.bid:.2f}, ask=${opt.ask:.2f}")
            break

    print(f"\n=== Jumping to Next Day ===")
    engine.jump_to_next_day()

    print(f"\n=== Day 2 ===")
    print(f"Option chain size: {len(engine.option_chain)}")

    print(f"\nChecking option chain AFTER jump:")
    found_match_after = False
    for opt in engine.option_chain:
        if (opt.strike == pos.strike and
            opt.option_type == pos.option_type and
            opt.expiration == pos.expiration):
            print(f"  ✓ Found matching option: exp={opt.expiration}, mid=${opt.mid:.2f}")
            found_match_after = True
            break
    if not found_match_after:
        print(f"  ✗ NO MATCHING OPTION IN CHAIN")
        print(f"  Looking for: strike={pos.strike}, type={pos.option_type}, exp={pos.expiration}")
        print(f"  Sample expirations in chain:")
        shown = 0
        for opt in engine.option_chain:
            if opt.strike == pos.strike and opt.option_type == pos.option_type and shown < 3:
                print(f"    - {opt.expiration}")
                shown += 1

    print(f"\nSpot price: ${engine.current_spot_price:.2f}")
    print(f"Current time: {engine.current_time}")
    print(f"Day index: {engine.current_day_index}")

    assert len(engine.portfolio_manager.open_positions) == 1, "Position disappeared"
    pos_after = engine.portfolio_manager.open_positions[0]

    print(f"\nPosition after jump:")
    print(f"  Entry: ${pos_after.entry_price:.2f}")
    print(f"  Current: ${pos_after.current_price:.2f}")
    print(f"  P&L: ${pos_after.get_pnl():.2f}")

    print(f"\n=== Comparison ===")
    print(f"Entry price changed: {entry_price} -> {pos_after.entry_price} (should stay same)")
    print(f"Current price changed: {initial_current_price} -> {pos_after.current_price} (should change)")
    print(f"P&L changed: {initial_pnl} -> {pos_after.get_pnl()} (should change)")

    assert pos_after.entry_price == entry_price, "Entry price should not change"

    if abs(engine.current_spot_price - initial_spot) > 0.01:
        print(f"\n✓ Spot moved from ${initial_spot:.2f} to ${engine.current_spot_price:.2f}")

        different_current = abs(pos_after.current_price - initial_current_price) > 0.01
        print(f"✓ Current price {'CHANGED' if different_current else 'DID NOT CHANGE'}: ${initial_current_price:.2f} -> ${pos_after.current_price:.2f}")

        if not different_current:
            print(f"\n❌ PROBLEM: Current price did not update when jumping to next day!")
            print(f"   This means update_positions() was not called or option_chain was not regenerated")
            return False

        different_pnl = abs(pos_after.get_pnl() - initial_pnl) > 0.01
        print(f"✓ P&L {'CHANGED' if different_pnl else 'DID NOT CHANGE'}: ${initial_pnl:.2f} -> ${pos_after.get_pnl():.2f}")

        if not different_pnl:
            print(f"\n❌ PROBLEM: P&L did not change even though current price changed!")
            return False
    else:
        print(f"\n⚠ WARNING: Spot barely moved, can't verify P&L update")

    print(f"\n✓ Test PASSED")
    return True


if __name__ == "__main__":
    try:
        result = test_jump_next_day_updates_pnl()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

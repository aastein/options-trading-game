# Testing Documentation

## Test Suite Overview

Comprehensive test suite with 25 tests covering all critical components.

## Running Tests

```bash
python run_tests.py
```

## Test Coverage

### 1. Trading Calendar Tests (7 tests)
- `test_is_trading_day_weekday` - Validates weekday detection
- `test_is_trading_day_weekend` - Validates weekend exclusion
- `test_is_trading_day_holiday` - Validates holiday exclusion
- `test_next_trading_day` - Validates trading day iteration
- `test_generate_trading_days` - Validates 252 day generation
- `test_get_weekly_expirations` - Validates Friday expirations
- `test_get_monthly_expiration` - Validates third Friday calculation

### 2. Regime Generator Tests (2 tests)
- `test_generate_regime_sequence` - Validates HMM state transitions
- `test_generate_daily_ohlc` - Validates OHLC constraints (H≥O, H≥C, L≤O, L≤C)

### 3. Tick Generator Tests (1 test)
- `test_generate_day_ticks` - Validates 4,680 tick generation with OHLC constraints

### 4. Black-Scholes Pricer Tests (7 tests)
- `test_call_price_atm` - Validates call pricing
- `test_put_price_atm` - Validates put pricing
- `test_call_delta` - Validates call delta (0 < δ < 1)
- `test_put_delta` - Validates put delta (-1 < δ < 0)
- `test_gamma` - Validates gamma calculation
- `test_zero_expiry_call_itm` - Validates intrinsic value at expiration
- `test_zero_expiry_call_otm` - Validates zero value for OTM at expiration

### 5. Portfolio Manager Tests (5 tests)
- `test_initial_state` - Validates starting capital
- `test_buy_option` - Validates order execution and cash deduction
- `test_buy_insufficient_cash` - Validates margin checks
- `test_sell_option` - Validates position closing
- `test_get_total_value` - Validates portfolio valuation

### 6. Integration Tests (3 tests)
- `test_full_pipeline` - End-to-end test: generation → pricing → trading
- `test_day_generation_performance` - Validates <500ms day initialization
- `test_chain_generation_performance` - Validates <100ms chain generation

## Bugs Fixed

### Bug #1: Array Truth Value Ambiguity
**File:** `app.py:250`
**Error:** `ValueError: The truth value of an array with more than one element is ambiguous`
**Fix:** Changed `if not self.current_day_ticks:` to `if len(self.current_day_ticks) == 0:`

### Bug #2: FBM Shape Mismatch
**File:** `market/fbm_bridge.py:39`
**Error:** `ValueError: operands could not be broadcast together with shapes (1980,) (1981,)`
**Fix:** FBM library generates n+1 points for n increments. Changed to request `n_steps-1` to get exactly `n_steps` output.

### Bug #3: Tick Count Off by 2
**File:** `market/fbm_bridge.py:75-76`
**Error:** Generated 4,678 ticks instead of 4,680
**Fix:** Added +1 to segment lengths to account for overlap removal: `low_idx - high_idx + 1` and `n_ticks - low_idx + 1`

## Pre-Run Checklist

Before running `python app.py`:

1. ✓ Activate virtual environment
2. ✓ Install all dependencies (`pip install -r requirements.txt`)
3. ✓ Run calibration (`python -m calibration.calibration_runner --tickers SPY QQQ IWM`)
4. ✓ Run test suite (`python run_tests.py`) - All 25 tests must pass
5. ✓ Verify config files exist in `config/` directory

## Test Results (Latest Run)

```
Ran 25 tests in 0.162s

OK
```

**Status:** ✓ All tests passing
**Performance:** 
- Day generation: <200ms ✓
- Chain generation: <100ms ✓
- Memory usage: <50MB ✓

## Continuous Testing

Run tests before commits:
```bash
python run_tests.py && echo "✓ Ready to commit"
```

## Adding New Tests

1. Create test file in `tests/` directory following pattern `test_*.py`
2. Import unittest and relevant modules
3. Create test class inheriting from `unittest.TestCase`
4. Add test methods starting with `test_`
5. Run `python run_tests.py` to verify

## Dependencies Verified

- PySide6 ✓
- yfinance ✓
- numpy ✓
- scipy ✓
- pandas ✓
- hmmlearn ✓
- fbm ✓
- py_vollib ✓

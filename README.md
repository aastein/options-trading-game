# Option Trading Game - Synthetic Market Simulator

A standalone PySide6 application that generates realistic synthetic market data and option chains for SPY, QQQ, and IWM, allowing users to practice options trading with configurable capital and performance tracking.

## Features

- **Realistic Market Generation**: Hidden Markov Model for regime-based daily returns
- **Intraday Simulation**: 4,680 5-second ticks per day using fractional Brownian motion
- **Full Option Chains**: Black-Scholes pricing with calibrated IV surface and Greeks
- **Portfolio Management**: Track positions, P&L, margin, and performance metrics
- **Time Controls**: Play/pause, speed adjustment, jump forward to midday/close/next day
- **Real Trading Calendar**: Respects NYSE/NASDAQ holidays and market hours

## Installation

### 1. Create Virtual Environment

```bash
cd option-trader-game
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Calibrate Tickers

Before running the game, you must calibrate the tickers. This downloads historical data and fits the models.

```bash
python -m calibration.calibration_runner --tickers SPY QQQ IWM
```

This will:
- Download max available historical data from yfinance
- Fit Hidden Markov Models (4 states)
- Calculate distribution parameters
- Estimate IV surface parameters
- Save configurations to `config/` directory

**Estimated runtime**: 2-5 minutes per ticker

### Step 2: Run the Game

```bash
python app.py
```

This will:
1. Show a setup dialog to select ticker and starting capital
2. Generate 252 trading days of synthetic market data
3. Initialize the portfolio and option chains
4. Display the main trading interface

## Game Interface

### Top Status Bar
- **Current Time**: Simulation timestamp
- **Portfolio Value**: Total account value (cash + positions)
- **P&L**: Total profit/loss
- **Margin**: Required vs. available margin

### Left Panel - Market Data
- Ticker selector (SPY/QQQ/IWM)
- Current spot price
- Daily OHLC

### Center Panel - Option Chain
- Tabbed by expiration (DTE shown)
- Columns: Call Bid/Ask/Mid/IV/Delta, Strike, Put Delta/IV/Mid/Ask/Bid
- **Double-click** any option to open order dialog
- Select buy/sell and quantity

### Right Panel - Portfolio
- **Metrics**: Cash, Total Value, P&L, ROI, Sharpe, Max Drawdown
- **Open Positions**: Real-time mark-to-market P&L
- Position details: ticker, expiration, strike, type, quantity

### Bottom Controls
- **Play/Pause**: Start/stop tick playback
- **Speed**: 1x, 2x, 5x
- **Jump to 1:00 PM**: Skip to midday same day
- **Jump to Close**: Skip to 4:00 PM same day
- **Jump to Next Day**: Skip to next trading day 9:30 AM
- **Progress Bar**: Current position in trading day

## Trading Mechanics

### Order Execution
- Orders execute instantly at mid-price
- Bid-ask spread: 2-3% for ATM, 5-10% for OTM
- Margin requirement: 15% of absolute delta dollars

### Position Management
- Mark-to-market updates every tick (5 seconds)
- Automatic expiration handling at 4:00 PM
- ITM options auto-exercised, OTM expire worthless

### Performance Tracking
- **ROI**: (Current Value - Starting Capital) / Starting Capital
- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Max Drawdown**: Largest peak-to-trough decline

## Architecture

### Market Generation Pipeline
1. **Regime Model** (HMM): Daily return states (low-vol, normal, high-vol, extreme)
2. **Daily OHLC**: Sample from regime-specific distributions
3. **Intraday Ticks**: Fractional Brownian motion bridges constrained by OHLC
4. **Touch Times**: High/Low placement weighted by session segment

### Option Pricing
1. **IV Surface**: ATM base × term structure × moneyness skew
2. **Black-Scholes**: Calculate price and Greeks (delta, gamma, theta, vega, rho)
3. **Chain Generation**: Strikes at ±1%, ±2%, ±5%, ±10%, ±20% from spot
4. **Expirations**: Weekly (0-32 DTE) + Monthly (~60 DTE)

### Portfolio Margin
- Delta Dollars = Σ(position_qty × delta × 100 × spot_price)
- Required Margin = |Delta Dollars| × 15%
- Must maintain: Cash ≥ Required Margin

## Performance Targets

- Day initialization: <200ms
- Per-tick chain update: <10ms (every minute)
- Jump-forward calculation: <50ms
- Total memory: <50MB per game session

## File Structure

```
option-trader-game/
├── calibration/          # Historical data calibration
│   ├── hmm_calibrator.py
│   ├── distribution_calibrator.py
│   ├── iv_calibrator.py
│   └── calibration_runner.py
├── market/               # Synthetic data generation
│   ├── calendar.py
│   ├── regime_generator.py
│   ├── fbm_bridge.py
│   └── tick_generator.py
├── options/              # Option pricing
│   ├── bs_pricer.py
│   ├── iv_surface.py
│   ├── greeks.py
│   └── chain_generator.py
├── portfolio/            # Position management
│   ├── portfolio_manager.py
│   ├── margin_calculator.py
│   └── metrics.py
├── ui/                   # PySide6 interface
│   ├── main_window.py
│   ├── market_panel.py
│   ├── chain_panel.py
│   ├── portfolio_panel.py
│   └── controls_panel.py
├── utils/
│   ├── types.py
│   └── config_loader.py
├── config/               # Calibrated parameters (JSON)
└── app.py                # Main entry point
```

## Troubleshooting

### "Configuration for {ticker} not found"
Run calibration first:
```bash
python -m calibration.calibration_runner --tickers SPY
```

### Import Errors
Ensure virtual environment is activated:
```bash
source venv/bin/activate
```

### Slow Performance
- Close other applications
- Reduce playback speed
- Use jump controls instead of playing through entire day

## Future Enhancements

- Multi-leg order entry (spreads, iron condors)
- Historical trade analysis
- Strategy backtesting mode
- Additional tickers (individual stocks)
- Save/load game state
- Leaderboard and scoring system

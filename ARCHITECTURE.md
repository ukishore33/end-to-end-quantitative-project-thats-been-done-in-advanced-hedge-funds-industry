# System Architecture

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA ACQUISITION LAYER                          │
│  (Yahoo Finance, IEX Cloud, Real-time feeds)                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DATA PROCESSING LAYER                             │
│  (Cleaning, normalization, feature engineering)                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    ┌────────┐       ┌────────┐         ┌────────┐
    │Strategy│       │Strategy│    ...  │Strategy│
    │   1    │       │   2    │         │   N    │
    │(MR)    │       │(MOM)   │         │(ML)    │
    └────────┘       └────────┘         └────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 SIGNAL AGGREGATION LAYER                            │
│  (Combine signals, apply ensemble logic)                           │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  RISK MANAGEMENT LAYER                              │
│  (Position sizing, portfolio optimization, VaR checks)            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXECUTION LAYER                                  │
│  (Paper trading, live trading, order management)                   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 MONITORING & REPORTING                              │
│  (Dashboard, alerts, performance metrics, logging)                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module Descriptions

### 1. Data Layer (`src/data/`)

**Purpose**: Unified interface for market data acquisition and preprocessing.

**Key Components**:
- `loaders.py`: Data ingestion from multiple sources
  - Yahoo Finance (free historical data)
  - IEX Cloud (optional, real-time updates)
  - CSV/Parquet local files
  
- `preprocessor.py`: Data cleaning and normalization
  - Handle missing data (forward fill, interpolation)
  - Outlier detection and treatment
  - Normalization (returns, log returns)
  
- `features.py`: Technical indicator calculation
  - Moving averages (SMA, EMA, WMA)
  - Momentum indicators (RSI, MACD, Stochastic)
  - Volatility measures (ATR, Historical Vol, Bollinger Bands)
  - Correlation matrices, beta calculation
  
- `database.py`: Persistence layer
  - SQLite for historical data caching
  - Parquet for fast analytics
  - TimescaleDB option for production

**Interfaces**:
```python
# Loading data
data = MarketDataLoader.load(
    symbols=['AAPL', 'MSFT'],
    start='2020-01-01',
    end='2023-12-31',
    frequency='daily'
)

# Computing features
features = FeatureEngine.compute(
    data,
    indicators=['SMA_20', 'RSI_14', 'MACD', 'ATR_14']
)
```

---

### 2. Strategy Layer (`src/strategies/`)

**Purpose**: Signal generation from market data.

**Architecture**:

```python
class BaseStrategy(ABC):
    """Abstract base for all strategies"""
    @abstractmethod
    def generate_signals(self, market_data) -> pd.DataFrame:
        """Returns DataFrame with columns: [symbol, timestamp, signal, confidence]"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> dict:
        """Return strategy hyperparameters"""
        pass
```

**Implemented Strategies**:

1. **Mean Reversion** (`mean_reversion.py`)
   - Logic: Buy when price < MA - (k × σ), sell when price > MA + (k × σ)
   - Parameters: window (20-60), k (1-3), holding_period
   - Use case: Stationary markets, range-bound assets

2. **Momentum** (`momentum.py`)
   - Logic: Buy when price uptrend confirmed, sell on reversal signals
   - Parameters: lookback (10-30), threshold (0.02-0.05)
   - Use case: Trending markets, breakout strategies

3. **ML Ensemble** (`ml_strategy.py`)
   - Models: Random Forest (tree ensemble), XGBoost, LSTM (time series)
   - Features: Technical indicators + macro factors
   - Logic: Ensemble voting with confidence weighting
   - Parameters: model_type, lookback, prediction_horizon

**Signal Format**:
```python
{
    'timestamp': datetime,
    'symbol': str,
    'signal': float,  # -1.0 to +1.0 (short to long)
    'confidence': float,  # 0.0 to 1.0
    'reason': str  # Human-readable explanation
}
```

---

### 3. Backtesting Engine (`src/backtesting/`)

**Purpose**: Simulate historical strategy performance with realistic constraints.

**Architecture**:

```
BacktestEngine
├── Portfolio (holdings, cash, NAV tracking)
├── OrderManager (queue, execution, fills)
├── TransactionCosts (commissions, slippage, market impact)
└── MetricsComputer (Sharpe, Sortino, Drawdown, etc.)
```

**Key Features**:
- **Event-driven simulation**: Process market data chronologically
- **Realistic execution**:
  - Fixed commission: 0.001% (IB-like)
  - Slippage model: 1-5 bps based on volume
  - Market impact: 0.01-0.05 bps per dollar traded
  
- **Portfolio tracking**:
  - Position tracking (long/short, avg price)
  - Mark-to-market revaluation
  - Leverage and margin requirements
  - Cash management and dividends (optional)

**API**:
```python
engine = BacktestEngine(
    initial_capital=1_000_000,
    commission=0.001,  # 0.001%
    slippage_bps=2.0,
    use_bid_ask=False  # Use close price
)

results = engine.run(
    strategies=[mean_reversion_strategy, momentum_strategy],
    market_data=price_data,
    start_date='2020-01-01',
    end_date='2023-12-31'
)

# Returns: BacktestResults object
results.get_metrics()  # Sharpe, Sortino, MDD, etc.
results.get_trades()   # Trade log
results.get_portfolio_values()  # Daily NAV
```

---

### 4. Risk Management (`src/risk/`)

**Purpose**: Portfolio-level risk control and optimization.

**Components**:

1. **Optimizer** (`optimizer.py`)
   - Markowitz Mean-Variance Optimization
   - Min variance portfolio, max Sharpe, risk parity
   - Constraints: sector limits, position limits, leverage bounds
   
2. **Risk Metrics** (`metrics.py`)
   - **Value at Risk (VaR)**: 95th percentile loss
   - **Conditional VaR (CVaR)**: Average loss beyond VaR
   - **Greeks**: Delta, Gamma (for derivatives)
   - **Concentration**: Herfindahl index, sector exposure
   
3. **Position Sizing** (`position_sizing.py`)
   - Kelly Criterion: Optimal position size for given edge
   - Volatility scaling: Size inversely to realized volatility
   - Confidence-weighted sizing: Scale by signal confidence
   
4. **Alerts** (`alerts.py`)
   - Daily VaR breach alerts
   - Sector concentration violations
   - Liquidity checks (position size vs. avg volume)
   - Circuit breakers (halt trading on extreme losses)

**Example**:
```python
risk_manager = RiskManager(
    max_var_daily=0.02,  # 2% daily VaR limit
    max_sector_exposure=0.25,  # 25% per sector
    max_position_size=0.05,  # 5% per position
    confidence_level=0.95
)

# Optimize portfolio weights
optimal_weights = risk_manager.optimize(
    expected_returns=estimated_returns,
    covariance_matrix=cov_matrix,
    constraints={'min_weight': 0.01, 'max_weight': 0.10'}
)

# Check if trade violates risk limits
is_safe = risk_manager.validate_trade(
    symbol='AAPL',
    quantity=10000,
    current_price=150.0,
    market_data=recent_data
)
```

---

### 5. Execution Layer (`src/execution/`)

**Purpose**: Trade order management and execution.

**Components**:

1. **Paper Trader** (`paper_trader.py`)
   - Simulates order execution without real capital
   - Fills at next bar's close price
   - Tracks realized/unrealized P&L
   - Use for strategy testing, training

2. **Live Trader** (`live_trader.py`)
   - Interfaces with brokers (Alpaca, IB, etc.)
   - Real-time order placement and tracking
   - Position reconciliation
   - Emergency stop-loss execution

3. **Order Manager** (`order_manager.py`)
   - Order queue and priority
   - Partial fill handling
   - Rejection and retry logic
   - Order history and audit trail

4. **Commissions** (`commissions.py`)
   - Per-broker fee schedules
   - Volume-based discounts
   - Options pricing models

---

### 6. Monitoring (`src/monitoring/`)

**Purpose**: Real-time tracking and alerting.

**Components**:

1. **Dashboard** (`dashboard.py`)
   - Streamlit interactive web UI
   - Real-time P&L, Greeks, risk metrics
   - Trade logs, strategy performance
   - Heatmaps: correlations, sector performance
   - Drilldown: individual position analysis

2. **Alerts** (`alerts.py`)
   - Email/Slack notifications for:
     - Large losses, large gains
     - Risk limit breaches
     - Execution failures
     - Liquidity issues

3. **Logger** (`logger.py`)
   - Structured logging (JSON format)
   - Log levels: DEBUG, INFO, WARNING, ERROR
   - Rotation and archival
   - Correlation IDs for request tracing

4. **Metrics Server** (`metrics_server.py`)
   - Prometheus metrics export
   - Integration with monitoring stacks (Grafana)
   - System health checks

---

## Workflow Examples

### Example 1: Daily Backtest Cycle

```python
# 1. Load data
data = MarketDataLoader.load(
    symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
    start='2020-01-01',
    end='2023-12-31'
)

# 2. Prepare features
features = FeatureEngine.compute(
    data, 
    indicators=['SMA_20', 'RSI_14', 'MACD']
)

# 3. Initialize strategies
mr_strategy = MeanReversionStrategy(window=30, k=2.0)
mom_strategy = MomentumStrategy(lookback=20)
ml_strategy = MLStrategy(model='xgboost')

# 4. Run backtest
engine = BacktestEngine(initial_capital=1_000_000)
results = engine.run(
    strategies=[mr_strategy, mom_strategy, ml_strategy],
    data=data,
    features=features
)

# 5. Analyze results
print(f"Sharpe: {results.sharpe_ratio}")
print(f"Max Drawdown: {results.max_drawdown}")
print(f"Win Rate: {results.win_rate}")

# 6. Generate report
report = PerformanceReport(results)
report.to_html('backtest_report.html')
report.to_excel('backtest_results.xlsx')
```

### Example 2: Live Trading Execution

```python
# 1. Initialize live trader
trader = LiveTrader(
    broker='alpaca',
    api_key=os.getenv('ALPACA_API_KEY'),
    config=execution_config
)

# 2. Risk manager
risk_mgr = RiskManager(max_daily_loss=0.02)

# 3. Main trading loop
while True:
    # Get latest market data
    data = get_market_data()
    
    # Generate signals
    signals = strategy.generate_signals(data)
    
    # Validate against risk limits
    for signal in signals:
        if risk_mgr.validate_trade(signal):
            # Place order
            order = trader.place_order(
                symbol=signal['symbol'],
                quantity=signal['quantity'],
                side='BUY' if signal['signal'] > 0 else 'SELL'
            )
            logger.info(f"Order placed: {order.id}")
    
    # Monitor portfolio
    portfolio = trader.get_portfolio()
    dashboard.update(portfolio)
    
    # Check for alerts
    if portfolio.daily_loss > 0.02:
        alerts.send_email("Daily loss limit breached!")
        break
    
    # Sleep until next bar
    time.sleep(60)
```

---

## Performance Considerations

### Optimization Strategies

1. **Vectorization**: Use NumPy/Pandas operations instead of loops
   ```python
   # Slow (Python loop)
   for i in range(len(prices)):
       returns[i] = (prices[i] - prices[i-1]) / prices[i-1]
   
   # Fast (Vectorized)
   returns = prices.pct_change()
   ```

2. **Caching**: Store computed features and models
   ```python
   @lru_cache(maxsize=128)
   def compute_features(symbol, date):
       ...
   ```

3. **Parallel Processing**: Backtest multiple strategies simultaneously
   ```python
   with ProcessPoolExecutor(max_workers=4) as executor:
       results = executor.map(backtest_strategy, strategies)
   ```

4. **Database Indexing**: Speed up time-series queries
   ```sql
   CREATE INDEX idx_symbol_date ON market_data(symbol, date);
   ```

---

## Testing Strategy

1. **Unit Tests**: Individual functions (95%+ coverage)
2. **Integration Tests**: End-to-end workflows
3. **Property-Based Tests**: Use Hypothesis library
4. **Backtesting**: Historical validation
5. **Paper Trading**: Live environment simulation
6. **Stress Tests**: Extreme market conditions

---

## Deployment

### Development
```bash
python -m pytest tests/ -v --cov
streamlit run src/monitoring/dashboard.py
```

### Production
```bash
docker build -t hedge-fund-algo .
docker run -e API_KEY=$API_KEY hedge-fund-algo
```

### Monitoring
- Prometheus for metrics
- ELK stack for logging
- Grafana dashboards
- PagerDuty for alerts

---

## Scaling Considerations

1. **Data**: Move to TimescaleDB or InfluxDB for large volumes
2. **Computation**: GPU acceleration for ML models (CUDA, TensorFlow)
3. **Trading**: Async order execution, message queues (RabbitMQ)
4. **Storage**: S3 for backtest results, data versioning with DVC
5. **Infrastructure**: Kubernetes orchestration for distributed systems

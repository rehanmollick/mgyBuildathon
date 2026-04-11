# API REFERENCE

QuantForge exposes four HTTP endpoints. All endpoints accept and return JSON. All request bodies are validated by pydantic before reaching the orchestrator. All responses include a request ID for traceability.

Base URL: `http://127.0.0.1:8000` (local) or your deployment URL.

## Authentication

v1 is anonymous. No API keys required. v3 adds user accounts and scoped API keys. See `docs/ROADMAP.md`.

## Rate limits

v1 has no enforced rate limits. v3 introduces tiered rate limits:

| Tier         | Requests/minute | Requests/day |
|--------------|-----------------|--------------|
| Free         | 10              | 100          |
| Individual   | 60              | 1,000        |
| Team         | 600             | 10,000       |
| Enterprise   | custom          | custom       |

## Common response headers

| Header            | Purpose |
|-------------------|---------|
| `X-Request-ID`    | Unique ID for the request, echoed in logs |
| `X-QuantForge-Version` | Server version, e.g. `0.1.0` |
| `Content-Type`    | Always `application/json` for JSON responses |

## Error format

All errors return JSON with the following shape:

```json
{
  "error": {
    "code": "STRATEGY_PARSE_ERROR",
    "message": "Function signature does not match required shape",
    "details": {
      "expected": "def strategy(df: pd.DataFrame) -> pd.Series",
      "received": "def my_strategy(data):"
    },
    "request_id": "req_abc123..."
  }
}
```

### Error codes

| Code                      | HTTP status | Meaning |
|---------------------------|:-----------:|---------|
| `STRATEGY_PARSE_ERROR`    |     400     | Agent 1 could not produce valid Python from the description |
| `STRATEGY_EXECUTION_ERROR`|     400     | The strategy code raised an exception when executed |
| `STRATEGY_TIMEOUT`        |     400     | The strategy code exceeded `QUANTFORGE_EXEC_TIMEOUT` |
| `INVALID_ASSET`           |     400     | The asset ticker is not supported |
| `MODEL_UNAVAILABLE`       |     503     | An upstream model (Claude, Kronos, VibeVoice) is not reachable |
| `RATE_LIMITED`            |     429     | Request rate exceeded tier limits |
| `VALIDATION_ERROR`        |     422     | Request body failed pydantic validation |
| `INTERNAL_ERROR`          |     500     | Unexpected server error |

## Endpoints

### POST /api/forge

Run the main stress-test pipeline: parse the strategy, imagine 200 markets, backtest against all of them, return a verdict.

**Request body:**

```json
{
  "description": "Buy when the 50-day moving average crosses above the 200-day, sell on the cross below",
  "asset": "SPY",
  "n_scenarios": 200
}
```

| Field         | Type   | Required | Default | Description |
|---------------|--------|----------|---------|-------------|
| `description` | string | yes      | —       | Plain-English strategy description, max 2000 chars |
| `asset`       | string | no       | `SPY`   | Ticker symbol. v1 supports `SPY` only; v2 adds more |
| `n_scenarios` | int    | no       | 200     | Number of synthetic market histories to generate. Min 20, max 1000 |

**Response:**

```json
{
  "request_id": "req_abc123",
  "code": "def strategy(df):\n    ...",
  "summary": "Your strategy returned 40% on real SPY data...",
  "result": {
    "real": {
      "total_return": 0.40,
      "max_drawdown": -0.12,
      "sharpe": 1.8,
      "equity_curve": [1.0, 1.002, ...]
    },
    "synthetic": {
      "total_return_distribution": [0.02, -0.11, 0.34, ...],
      "max_drawdown_distribution": [-0.15, -0.22, ...],
      "sharpe_distribution": [0.3, 1.1, ...],
      "percentile_bands": {
        "timestamps": ["2023-07-01", ...],
        "p05": [1.0, 0.97, ...],
        "p50": [1.0, 1.01, ...],
        "p95": [1.0, 1.05, ...]
      },
      "ghost_lines": [[1.0, 1.02, ...], [1.0, 0.98, ...]]
    },
    "probability_of_ruin": 0.18,
    "overfitting_percentile": 94.3
  },
  "verdict": "Your strategy returned 40% on real SPY data..."
}
```

**Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/forge \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Buy when RSI drops below 30, sell when RSI crosses above 70",
    "asset": "SPY"
  }'
```

**Typical latency:** ~15 seconds on a warm backend with GBM generator.

---

### POST /api/evolve

Run the Evolve pipeline: parse the baseline, generate 10 mutated variants, backtest all 11 strategies against the same 200 synthetic markets, rank by overfitting percentile.

**Request body:**

```json
{
  "description": "Buy when RSI < 30, sell when RSI > 70",
  "asset": "SPY",
  "n_variants": 10
}
```

| Field         | Type   | Required | Default | Description |
|---------------|--------|----------|---------|-------------|
| `description` | string | yes      | —       | Plain-English baseline strategy description |
| `asset`       | string | no       | `SPY`   | Ticker symbol |
| `n_variants`  | int    | no       | 10      | Number of mutated variants. Min 2, max 20 |

**Response:**

```json
{
  "request_id": "req_def456",
  "baseline": {
    "description": "Buy when RSI < 30, sell when RSI > 70",
    "code": "def strategy(df): ...",
    "result": { ... same shape as /api/forge's result ... }
  },
  "variants": [
    {
      "rank": 1,
      "description": "RSI(14) < 30, sell when RSI(14) > 70, with 20-day volume filter",
      "code": "def strategy(df): ...",
      "result": { ... },
      "overfitting_percentile": 58.2
    },
    ...
  ],
  "verdict": "The most robust variant adds a volume filter..."
}
```

**Typical latency:** ~25 seconds on a warm backend (Kronos/GBM called once, 11 strategies backtested).

---

### POST /api/narrate

Synthesize the verdict text into spoken audio. Called in parallel with `/api/forge` or `/api/evolve` by the frontend.

**Request body:**

```json
{
  "verdict_text": "Your strategy returned 40% on real SPY data..."
}
```

| Field          | Type   | Required | Description |
|----------------|--------|----------|-------------|
| `verdict_text` | string | yes      | Text to synthesize, max 1000 chars |

**Response:**

```json
{
  "request_id": "req_ghi789",
  "audio_url": "/static/audio/verdict_a1b2c3.wav",
  "duration_seconds": 8.4,
  "source": "stub"
}
```

| Field              | Type   | Description |
|--------------------|--------|-------------|
| `audio_url`        | string | URL to the synthesized audio file, relative to server root |
| `duration_seconds` | float  | Length of the audio file |
| `source`           | string | `stub` in v1, `vibevoice` in v2 |

**Typical latency:** ~0.5s for stub, ~8s for live VibeVoice (v2).

---

### GET /api/health

Health check. Returns 200 if the backend is operational, 503 if any dependency is degraded.

**Response:**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "generator": "gbm",
  "anthropic_available": true,
  "kronos_available": false,
  "uptime_seconds": 12345
}
```

| Field                 | Type   | Description |
|-----------------------|--------|-------------|
| `status`              | string | `ok` or `degraded` |
| `version`             | string | Semantic version of the deployed backend |
| `generator`           | string | `gbm` or `kronos`, the currently configured generator |
| `anthropic_available` | bool   | Whether the Anthropic API is reachable |
| `kronos_available`    | bool   | Whether Kronos weights are loaded (v2 only) |
| `uptime_seconds`      | int    | Seconds since server start |

---

## Pydantic models (source of truth)

The canonical schema lives in `backend/models.py`. The relevant models:

```python
class ForgeRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=2000)
    asset: str = Field(default="SPY", pattern=r"^[A-Z]{1,6}$")
    n_scenarios: int = Field(default=200, ge=20, le=1000)

class BacktestMetrics(BaseModel):
    total_return: float
    max_drawdown: float
    sharpe: float
    equity_curve: list[float]

class PercentileBands(BaseModel):
    timestamps: list[str]
    p05: list[float]
    p50: list[float]
    p95: list[float]

class SyntheticDistribution(BaseModel):
    total_return_distribution: list[float]
    max_drawdown_distribution: list[float]
    sharpe_distribution: list[float]
    percentile_bands: PercentileBands
    ghost_lines: list[list[float]]

class BacktestResult(BaseModel):
    real: BacktestMetrics
    synthetic: SyntheticDistribution
    probability_of_ruin: float
    overfitting_percentile: float

class ForgeResult(BaseModel):
    request_id: str
    code: str
    summary: str
    result: BacktestResult
    verdict: str
```

See `docs/SCHEMA.md` for a more detailed field-by-field specification and examples.

## Versioning

v1 endpoints are stable under the `/api/` prefix. Breaking changes in v2 will ship under `/api/v2/`, and `/api/` will remain pinned to v1 for at least six months after v2 ships.

## Idempotency

`/api/forge`, `/api/evolve`, and `/api/narrate` are idempotent in the sense that the same request body produces the same (or statistically equivalent) response. However, the GBM generator is seeded per request, so two identical requests will produce statistically similar but not bit-identical synthetic market histories. This is intentional: pinning the seed to the request body would make the overfitting percentile artificially stable and hide real run-to-run variation.

For deterministic reproducibility (useful in tests), pass a `seed` field in the request body. This is an undocumented v1 convenience feature; in v2 it becomes an official field.

## Example: end-to-end workflow

```bash
# 1. Health check
curl http://127.0.0.1:8000/api/health

# 2. Run a stress test
curl -X POST http://127.0.0.1:8000/api/forge \
  -H "Content-Type: application/json" \
  -d '{"description":"Buy and hold SPY","asset":"SPY"}' \
  | jq '.result.overfitting_percentile'

# 3. Narrate the verdict in parallel (usually the frontend does this)
curl -X POST http://127.0.0.1:8000/api/narrate \
  -H "Content-Type: application/json" \
  -d '{"verdict_text":"Your strategy looks robust."}' \
  | jq '.audio_url'

# 4. Evolve the strategy
curl -X POST http://127.0.0.1:8000/api/evolve \
  -H "Content-Type: application/json" \
  -d '{"description":"Buy when RSI < 30, sell when RSI > 70"}' \
  | jq '.variants[].overfitting_percentile'
```

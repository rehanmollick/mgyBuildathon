# SCHEMA

This document defines the typed JSON contract between the QuantForge backend and frontend. The source of truth lives in `backend/models.py` (pydantic v2) and `frontend/src/lib/types.ts` (TypeScript). This file explains the shape, the invariants, and the rationale behind each field.

If you are adding a field, update both sides and add a golden round-trip test in `backend/tests/test_api_contracts.py`. See `docs/TESTING.md` for the test pattern.

## Why a typed contract

The frontend and backend are written in different languages and developed in parallel. Without a contract, drift is inevitable: a field gets renamed on one side, the other side quietly breaks, and the bug is only caught in production. QuantForge treats the schema as load-bearing. The backend serializes a pydantic model; the frontend parses the same shape into a TypeScript interface; the round-trip test pins both sides against a canonical fixture.

The contract is versioned via the URL prefix (`/api/` for v1). Breaking changes ship under `/api/v2/` and the v1 contract is frozen.

## Top-level request/response models

### `ForgeRequest`

```typescript
interface ForgeRequest {
  description: string;   // 10..2000 chars
  asset?: string;        // default "SPY", regex ^[A-Z]{1,6}$
  n_scenarios?: number;  // default 200, min 20, max 1000
  seed?: number;         // optional, for deterministic tests
}
```

Invariants:
- `description` is trimmed server-side before hashing or logging. Trailing whitespace must not change the request fingerprint.
- `asset` is always uppercased by pydantic before validation. A request with `asset: "spy"` is normalized to `"SPY"`.
- `n_scenarios` below 20 is rejected because the percentile bands are unstable with fewer than ~20 samples.

### `ForgeResult`

```typescript
interface ForgeResult {
  request_id: string;        // "req_" + 12 hex chars
  code: string;              // the generated strategy function
  summary: string;           // one-sentence summary from the Analyst
  result: BacktestResult;    // full metrics, see below
  verdict: string;           // multi-sentence narrative from the Analyst
}
```

`summary` is what appears inline in the UI (next to the "Forge" button result area). `verdict` is what the Narrator reads aloud. They are intentionally separate because the summary needs to be short for display and the verdict needs to be narratable for speech.

### `EvolveRequest`

```typescript
interface EvolveRequest {
  description: string;   // same constraints as ForgeRequest
  asset?: string;        // default "SPY"
  n_variants?: number;   // default 10, min 2, max 20
  seed?: number;
}
```

### `EvolveResult`

```typescript
interface EvolveResult {
  request_id: string;
  baseline: VariantResult;         // the user's original strategy
  variants: VariantResult[];       // up to n_variants, ranked by overfitting percentile
  verdict: string;                 // Analyst's comparison of baseline vs best variant
}

interface VariantResult {
  rank: number;                    // 1 = most robust
  description: string;             // Mutator's plain-English description of what changed
  code: string;
  result: BacktestResult;
  overfitting_percentile: number;
}
```

Variants are returned in rank order (rank 1 first). The baseline is not in the `variants` array; it's a separate field so the frontend can render it as the anchor row.

### `NarrateRequest` / `NarrateResponse`

```typescript
interface NarrateRequest {
  verdict_text: string;  // 1..1000 chars
}

interface NarrateResponse {
  request_id: string;
  audio_url: string;      // relative URL under /static/audio/
  duration_seconds: number;
  source: "stub" | "vibevoice";
}
```

`source` is always `"stub"` in v1 (a pre-recorded placeholder) and `"vibevoice"` in v2 when the live TTS is wired.

## Metric models

### `BacktestMetrics`

The metrics for a single run (real or synthetic):

```typescript
interface BacktestMetrics {
  total_return: number;      // decimal, 0.40 = 40%
  max_drawdown: number;      // decimal, negative (e.g., -0.12)
  sharpe: number;            // annualized, unitless
  equity_curve: number[];    // normalized to start at 1.0
}
```

Invariants:
- `equity_curve[0]` is always 1.0 (normalized starting capital).
- `equity_curve.length === len(price_data)` — one point per bar.
- `max_drawdown` is always <= 0 (or 0 for a monotonically rising curve).
- `sharpe` is NaN for zero-volatility curves; the frontend renders NaN as "—".

### `PercentileBands`

The shaded fan chart on the Forge dashboard:

```typescript
interface PercentileBands {
  timestamps: string[];     // ISO 8601 dates, one per bar
  p05: number[];            // 5th percentile equity curve
  p50: number[];            // median equity curve
  p95: number[];            // 95th percentile equity curve
}
```

Invariants:
- All four arrays have the same length.
- `p05[i] <= p50[i] <= p95[i]` for all i (by construction; if this fails, the stats module has a bug).
- Timestamps are monotonically increasing.

### `SyntheticDistribution`

The cloud of synthetic run results:

```typescript
interface SyntheticDistribution {
  total_return_distribution: number[];   // one per synthetic run
  max_drawdown_distribution: number[];
  sharpe_distribution: number[];
  percentile_bands: PercentileBands;
  ghost_lines: number[][];               // 20 sampled equity curves for display
}
```

Invariants:
- All three distribution arrays have the same length, equal to `n_scenarios` from the request.
- `ghost_lines.length === 20`. We sample 20 curves for the ghost overlay regardless of `n_scenarios` to keep the chart readable.
- `ghost_lines[i].length === percentile_bands.timestamps.length` for all i.

### `BacktestResult`

The full result object that the Backtester produces:

```typescript
interface BacktestResult {
  real: BacktestMetrics;
  synthetic: SyntheticDistribution;
  probability_of_ruin: number;         // 0.0..1.0, fraction of runs with max_drawdown < -0.5
  overfitting_percentile: number;      // 0.0..100.0, scipy.stats.percentileofscore(synthetic, real)
}
```

The `overfitting_percentile` is the headline metric. A value of 94.3 means the real-market run performed better than 94.3% of synthetic runs — a red flag, because if the strategy is genuinely robust, the real result should look like a typical synthetic result (near the 50th percentile).

## Error envelope

All errors share a single envelope:

```typescript
interface ErrorResponse {
  error: {
    code: ErrorCode;
    message: string;
    details?: Record<string, unknown>;
    request_id: string;
  };
}

type ErrorCode =
  | "STRATEGY_PARSE_ERROR"
  | "STRATEGY_EXECUTION_ERROR"
  | "STRATEGY_TIMEOUT"
  | "INVALID_ASSET"
  | "MODEL_UNAVAILABLE"
  | "RATE_LIMITED"
  | "VALIDATION_ERROR"
  | "INTERNAL_ERROR";
```

See `docs/API.md` for the HTTP status mapping. The frontend renders each code with a specific, actionable user message from `frontend/src/lib/errors.ts`. Never show the raw `code` to the user.

## Health response

```typescript
interface HealthResponse {
  status: "ok" | "degraded";
  version: string;              // semver
  generator: "gbm" | "kronos";
  anthropic_available: boolean;
  kronos_available: boolean;    // v2 only
  uptime_seconds: number;
}
```

Health is returned on 200 when `status === "ok"`, on 503 when `status === "degraded"` (e.g., Anthropic unreachable). The frontend uses this to show a "backend degraded" banner rather than hard-failing every request.

## Round-trip golden test

The contract is pinned by `backend/tests/test_api_contracts.py`:

```python
def test_forge_result_round_trip():
    canonical = ForgeResult(
        request_id="req_abc123def456",
        code="def strategy(df):\n    return pd.Series(0, index=df.index)",
        summary="Buy-and-hold strategy on SPY.",
        result=BacktestResult(...),
        verdict="Your strategy returned 40% on real SPY...",
    )
    json_str = canonical.model_dump_json()
    parsed = ForgeResult.model_validate_json(json_str)
    assert parsed == canonical
```

If a field is added to the model without updating the canonical fixture, this test fails. It has caught more real bugs than any other test in the suite.

## Frontend mirror

The frontend types live in `frontend/src/lib/types.ts` and are kept in sync manually. There is no codegen in v1 because the schema is small and codegen adds a build step for little benefit. v2 may introduce `datamodel-code-generator` or `openapi-typescript` depending on how the schema evolves.

The manual-sync rule: any PR that changes a pydantic model in `backend/models.py` must also change `frontend/src/lib/types.ts` in the same commit. CI runs a grep check that fails if `models.py` changed without `types.ts` changing.

## Design decisions

**Why decimals instead of percents?**
A `total_return` of `0.40` means 40%. We store decimals because they compose cleanly under multiplication (for compound returns) and they are the pandas/numpy default. The frontend formats as percent at render time.

**Why equity curves as `number[]` instead of `{timestamp, value}[]`?**
Storage efficiency. A 500-point equity curve is 4KB as a raw array, 40KB as an array of objects with ISO timestamps. For 200 synthetic curves that's 8MB vs 80KB. We align by index to a separate `timestamps` array and pay the denormalization cost once.

**Why separate `summary` and `verdict`?**
The summary is for visual display (tight, one sentence). The verdict is for speech (natural, narratable, multi-sentence). Combining them would force one of the two modes to compromise. Keeping them separate lets the Analyst optimize each independently.

**Why `overfitting_percentile` as 0-100 and not 0-1?**
Matches SciPy's `percentileofscore`. Users read percentiles as whole numbers ("94th percentile") not decimals ("0.94"). The frontend displays the raw value with a `°` suffix for visual emphasis.

**Why `ghost_lines.length === 20` and not `n_scenarios`?**
Rendering 200 lines in Recharts is slow and visually noisy. 20 lines with low opacity create the same "cloud" effect and render in under 100ms. The percentile bands carry the statistical weight; the ghost lines are purely for visual anchoring.

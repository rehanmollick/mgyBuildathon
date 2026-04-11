/**
 * Typed API contract — mirrors backend/models.py exactly.
 * See docs/SCHEMA.md for field-by-field rationale.
 */

export interface ForgeRequest {
  readonly description: string;
  readonly asset?: string;
  readonly n_scenarios?: number;
  readonly seed?: number;
}

export interface EvolveRequest {
  readonly description: string;
  readonly asset?: string;
  readonly n_variants?: number;
  readonly n_scenarios?: number;
  readonly seed?: number;
}

export interface NarrateRequest {
  readonly verdict_text: string;
}

export interface BacktestMetrics {
  readonly total_return: number;
  readonly max_drawdown: number;
  readonly sharpe: number;
  readonly equity_curve: readonly number[];
}

export interface PercentileBands {
  readonly timestamps: readonly string[];
  readonly p05: readonly number[];
  readonly p50: readonly number[];
  readonly p95: readonly number[];
}

export interface SyntheticDistribution {
  readonly total_return_distribution: readonly number[];
  readonly max_drawdown_distribution: readonly number[];
  readonly sharpe_distribution: readonly number[];
  readonly percentile_bands: PercentileBands;
  readonly ghost_lines: readonly (readonly number[])[];
}

export interface BacktestResult {
  readonly real: BacktestMetrics;
  readonly synthetic: SyntheticDistribution;
  readonly probability_of_ruin: number;
  readonly overfitting_percentile: number;
}

export interface ForgeResult {
  readonly request_id: string;
  readonly code: string;
  readonly summary: string;
  readonly result: BacktestResult;
  readonly verdict: string;
}

export interface VariantResult {
  readonly rank: number;
  readonly description: string;
  readonly code: string;
  readonly result: BacktestResult;
  readonly overfitting_percentile: number;
}

export interface EvolveResult {
  readonly request_id: string;
  readonly baseline: VariantResult;
  readonly variants: readonly VariantResult[];
  readonly verdict: string;
}

export interface NarrateResponse {
  readonly request_id: string;
  readonly audio_url: string;
  readonly duration_seconds: number;
  readonly source: "stub" | "vibevoice";
}

export interface HealthResponse {
  readonly status: "ok" | "degraded";
  readonly version: string;
  readonly generator: "gbm" | "kronos";
  readonly anthropic_available: boolean;
  readonly kronos_available: boolean;
  readonly uptime_seconds: number;
}

export type ErrorCode =
  | "STRATEGY_PARSE_ERROR"
  | "STRATEGY_EXECUTION_ERROR"
  | "STRATEGY_TIMEOUT"
  | "INVALID_ASSET"
  | "MODEL_UNAVAILABLE"
  | "RATE_LIMITED"
  | "VALIDATION_ERROR"
  | "INTERNAL_ERROR";

export interface ErrorDetail {
  readonly code: ErrorCode;
  readonly message: string;
  readonly details?: Readonly<Record<string, unknown>>;
  readonly request_id: string;
}

export interface ErrorResponse {
  readonly error: ErrorDetail;
}

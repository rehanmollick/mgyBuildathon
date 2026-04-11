/**
 * Frontend API client with a typed contract.
 *
 * Falls back to pre-computed fixtures when the backend is unreachable or
 * when NEXT_PUBLIC_DEMO_MODE=true. This keeps the demo working even without
 * a running backend, which is our insurance policy for the pitch.
 */

import { DEMO_EVOLVE_RESULT, DEMO_FORGE_RESULT } from "./fixtures";
import type {
  EvolveRequest,
  EvolveResult,
  ForgeRequest,
  ForgeResult,
  HealthResponse,
  NarrateRequest,
  NarrateResponse,
} from "./types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";

const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function post<TReq, TResp>(path: string, body: TReq): Promise<TResp> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    let code: string | undefined;
    try {
      const data = (await response.json()) as { error?: { code?: string; message?: string } };
      if (data.error?.message) {
        message = data.error.message;
      }
      code = data.error?.code;
    } catch {
      // ignore — use default status text
    }
    throw new ApiError(message, response.status, code);
  }
  return (await response.json()) as TResp;
}

export async function forge(req: ForgeRequest): Promise<ForgeResult> {
  if (DEMO_MODE) {
    return simulateLatency(DEMO_FORGE_RESULT);
  }
  try {
    return await post<ForgeRequest, ForgeResult>("/api/forge", req);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    return simulateLatency(DEMO_FORGE_RESULT);
  }
}

export async function evolve(req: EvolveRequest): Promise<EvolveResult> {
  if (DEMO_MODE) {
    return simulateLatency(DEMO_EVOLVE_RESULT);
  }
  try {
    return await post<EvolveRequest, EvolveResult>("/api/evolve", req);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    return simulateLatency(DEMO_EVOLVE_RESULT);
  }
}

export async function narrate(req: NarrateRequest): Promise<NarrateResponse> {
  try {
    return await post<NarrateRequest, NarrateResponse>("/api/narrate", req);
  } catch {
    return {
      request_id: "req_demo_narrate",
      audio_url: "/static/audio/verdict_demo.wav",
      duration_seconds: 8.4,
      source: "stub",
    };
  }
}

export async function health(): Promise<HealthResponse> {
  const response = await fetch(`${BACKEND_URL}/api/health`);
  if (!response.ok) {
    throw new ApiError(
      `${response.status} ${response.statusText}`,
      response.status,
    );
  }
  return (await response.json()) as HealthResponse;
}

async function simulateLatency<T>(value: T): Promise<T> {
  await new Promise((resolve) => setTimeout(resolve, 600));
  return value;
}

export { ApiError };

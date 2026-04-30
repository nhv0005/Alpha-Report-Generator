import type {
  AlphaReport,
  GenerateRequest,
  GenerationProgress,
  HealthResponse,
} from "./types";

const BASE_URL = "";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/api/health`, { cache: "no-store" });
  return handle<HealthResponse>(res);
}

// Module-level cache for the reports list.
// - In-flight de-dupe: concurrent callers share one fetch.
// - Success TTL: 30s — keeps the list snappy across navigation.
// - Failure TTL: 5s — stops a broken engine from being polled once per remount.
const REPORTS_SUCCESS_TTL_MS = 30_000;
const REPORTS_FAILURE_TTL_MS = 5_000;
let _reportsInFlight: Promise<AlphaReport[]> | null = null;
let _reportsCache: { at: number; data: AlphaReport[] } | null = null;
let _reportsError: { at: number; err: Error } | null = null;

export async function fetchReports(force = false): Promise<AlphaReport[]> {
  if (!force) {
    if (_reportsCache && Date.now() - _reportsCache.at < REPORTS_SUCCESS_TTL_MS) {
      return _reportsCache.data;
    }
    if (_reportsError && Date.now() - _reportsError.at < REPORTS_FAILURE_TTL_MS) {
      throw _reportsError.err;
    }
  }
  if (_reportsInFlight) return _reportsInFlight;
  _reportsInFlight = (async () => {
    try {
      const res = await fetch(`${BASE_URL}/api/alpha/reports`, { cache: "no-store" });
      const data = await handle<AlphaReport[]>(res);
      _reportsCache = { at: Date.now(), data };
      _reportsError = null;
      return data;
    } catch (e) {
      _reportsError = { at: Date.now(), err: e as Error };
      throw e;
    } finally {
      _reportsInFlight = null;
    }
  })();
  return _reportsInFlight;
}

export function invalidateReportsCache() {
  _reportsCache = null;
  _reportsError = null;
}

export async function fetchReport(id: string): Promise<AlphaReport> {
  const res = await fetch(`${BASE_URL}/api/alpha/reports/${id}`, { cache: "no-store" });
  return handle<AlphaReport>(res);
}

export async function generateReport(
  req: GenerateRequest
): Promise<{ report_id: string; status: string }> {
  const res = await fetch(`${BASE_URL}/api/alpha/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handle<{ report_id: string; status: string }>(res);
}

export async function fetchProgress(id: string): Promise<GenerationProgress> {
  const res = await fetch(`${BASE_URL}/api/alpha/status/${id}`, { cache: "no-store" });
  return handle<GenerationProgress>(res);
}

export async function deleteReport(id: string): Promise<{ deleted: boolean }> {
  const res = await fetch(`${BASE_URL}/api/alpha/reports/${id}`, { method: "DELETE" });
  return handle<{ deleted: boolean }>(res);
}

export async function cancelReport(
  id: string,
): Promise<{ cancelled: boolean; report_id: string; status: string }> {
  const res = await fetch(`${BASE_URL}/api/alpha/cancel/${id}`, { method: "POST" });
  invalidateReportsCache();
  return handle<{ cancelled: boolean; report_id: string; status: string }>(res);
}

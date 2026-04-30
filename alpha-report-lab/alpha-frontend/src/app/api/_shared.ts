export const PYTHON_SERVICE_URL =
  process.env.PYTHON_SERVICE_URL || "http://localhost:8000";

const TRACE_HEADERS = [
  "traceparent",
  "tracestate",
  "baggage",
  "x-dynatrace",
];

export const DEFAULT_TIMEOUT_MS = 15_000;

export function forwardedHeaders(req: Request): Record<string, string> {
  const out: Record<string, string> = { "Content-Type": "application/json" };
  for (const h of TRACE_HEADERS) {
    const v = req.headers.get(h);
    if (v) out[h] = v;
  }
  return out;
}

export async function proxyFetch(
  req: Request,
  path: string,
  init: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  try {
    return await fetch(`${PYTHON_SERVICE_URL}${path}`, {
      ...init,
      headers: { ...forwardedHeaders(req), ...(init.headers || {}) },
      signal: AbortSignal.timeout(timeoutMs),
      cache: "no-store",
    });
  } catch (err: any) {
    const reason =
      err?.name === "TimeoutError" || err?.cause?.code === "UND_ERR_HEADERS_TIMEOUT"
        ? `Upstream engine at ${PYTHON_SERVICE_URL} did not respond within ${timeoutMs}ms`
        : `Upstream engine at ${PYTHON_SERVICE_URL} unreachable: ${err?.message || err}`;
    return Response.json(
      { error: "engine_unavailable", detail: reason },
      { status: 503 },
    );
  }
}

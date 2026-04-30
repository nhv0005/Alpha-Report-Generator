import { PYTHON_SERVICE_URL, forwardedHeaders } from "../_shared";

export async function GET(req: Request) {
  let engine: any = { status: "unreachable" };
  try {
    const res = await fetch(`${PYTHON_SERVICE_URL}/health`, {
      headers: forwardedHeaders(req),
      cache: "no-store",
    });
    engine = await res.json();
  } catch (e: any) {
    engine = { status: "unreachable", error: e.message };
  }
  return Response.json({
    service: "alpha-report-frontend",
    status: "healthy",
    engine,
    timestamp: new Date().toISOString(),
  });
}

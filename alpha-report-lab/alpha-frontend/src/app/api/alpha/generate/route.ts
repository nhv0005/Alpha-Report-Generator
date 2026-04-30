import { PYTHON_SERVICE_URL, forwardedHeaders } from "../../_shared";

export async function POST(req: Request) {
  const body = await req.json();
  const res = await fetch(`${PYTHON_SERVICE_URL}/api/alpha/generate`, {
    method: "POST",
    headers: forwardedHeaders(req),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}

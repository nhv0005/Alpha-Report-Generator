import { PYTHON_SERVICE_URL, forwardedHeaders } from "../../../_shared";

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const res = await fetch(`${PYTHON_SERVICE_URL}/api/alpha/status/${params.id}`, {
    headers: forwardedHeaders(req),
    cache: "no-store",
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}

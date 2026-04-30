import { PYTHON_SERVICE_URL, forwardedHeaders } from "../../../_shared";

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const res = await fetch(`${PYTHON_SERVICE_URL}/api/alpha/reports/${params.id}`, {
    headers: forwardedHeaders(req),
    cache: "no-store",
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}

export async function DELETE(req: Request, { params }: { params: { id: string } }) {
  const res = await fetch(`${PYTHON_SERVICE_URL}/api/alpha/reports/${params.id}`, {
    method: "DELETE",
    headers: forwardedHeaders(req),
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}

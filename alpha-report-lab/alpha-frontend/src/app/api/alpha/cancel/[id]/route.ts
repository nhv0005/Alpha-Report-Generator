import { proxyFetch } from "../../../_shared";

export async function POST(req: Request, { params }: { params: { id: string } }) {
  const res = await proxyFetch(req, `/api/alpha/cancel/${params.id}`, { method: "POST" });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}

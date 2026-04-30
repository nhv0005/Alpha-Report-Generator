import { proxyFetch } from "../../_shared";

export async function GET(req: Request) {
  const res = await proxyFetch(req, "/api/alpha/reports");
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
